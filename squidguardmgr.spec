%define EL_REL %(UNAMER=$(uname -r); echo ${UNAMER##*.})
%{!?dist:%if "%{EL_REL}" == "el5"
%define dist .el5
%endif}
%{!?_with_squidguard:%{!?_without_squidguard:%define _with_squidguard --with-squidguard}}
%if 0%{?_with_squidclamav6:1}
%undefine _with_squidclamav5
%define _without_squidclamav5 --without-squidclamav5
%endif
Name:           squidguardmgr
Version:        1.14
Release:        1%{?dist}
Summary:        Web GUI for SquidGuard and SquidClamav administration

Group:          Applications/System
License:        GPLv3+
URL:            http://squidguardmgr.darold.net/
Source0:        http://downloads.sourceforge.net/project/%{name}/%{version}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
Vendor:         Gilles Darold <gilles @nospam@ darold.net>
Packager:       Tatsuya Nonogaki <winfield @nospam@ support.email.ne.jp>

# RPMBUILD USAGE
# --with squidclamav6  : builds for use with squidclamav 6.x
# --with squidclamav5  : builds for use with squidclamav 5.x
# Above two are exclusive. If both are erroneously specified, squidclamav6 wins.
# --without squidguard : doesn't count on squidGuard support - Use in conjunction
#                        with one of the above
# By default, only "--with squidguard" is implicitly enabled.
# Note that clamd, squidclamav, c-icap socks paths, etc. may vary per systems,
# check definitions below and also %%build section.

%define squidguard_bin /usr/bin/squidGuard
%define clamd_bin /usr/sbin/clamd
%define c_icap_bin /usr/bin/c-icap
%define squidclamav_bin /usr/local/bin/squidclamav
%define squidclamav_lib /usr/lib/c_icap/squidclamav.so
%define wwwdir sgmgr
%define squiduid squid
%define squidgid squid

BuildRequires:  perl, perl(ExtUtils::MakeMaker), gcc
%if 0%{?_with_squidguard:1}
BuildRequires:  %{squidguard_bin}
Requires:       %{squidguard_bin}
%endif
%if 0%{?_with_squidclamav5:1}
BuildRequires:  %{squidclamav_bin}
Requires:       %{clamd_bin}, %{squidclamav_bin}
%endif
%if 0%{?_with_squidclamav6:1}
BuildRequires:  %{squidclamav_lib}
Requires:       %{clamd_bin}, %{squidclamav_lib}, %{c_icap_bin}
%endif
Requires:       perl, squid
Requires:       httpd >= 2.2, mod_perl

%description
SquidGuard Manager is a Perl CGI Web GUI for squidGuard and SquidClamav
administration. It allows full management of SquidGuard blocklist and
ACLs. You can also manage graphicaly your SquidClamav configuration.

This program supports all configuration directives of SquidGuard and
SquidClamav without intrusive modification, i-e you can still edit the
configuration files by hand before and after using SquidGuard Manager.

%prep
%setup -q

%build
%{__perl} Makefile.PL \
%{?_without_squidguard:SQUIDGUARD=off} \
%{?_with_squidguard:SQUIDGUARD=%{squidguard_bin}} \
WWWDIR=/var/www/%{wwwdir} \
LANGDIR=en_US \
BASEURL=/squidguardmgr \
SQUIDUSR=%{squiduid} SQUIDGRP=%{squidgid} \
%{!?_with_squidclamav6:%{!?_with_squidclamav5:SQUIDCLAMAV=off}} \
%{?_with_squidclamav6:CICAP_SOCKET=/var/run/c-icap/c-icap.ctl} \
%{?_with_squidclamav5:%{!?_without_squidclamav5:SQUIDCLAMAV=%{squidclamav_bin}}} \
DESTDIR=$RPM_BUILD_ROOT \
QUIET=1

%{__make}

%install
%define el6htcont contrib/EL6/httpd
%if "%{EL_REL}" == "el5"
%{__perl} -pi.orig -e 's|^(PIDFILE=/var/run)/httpd(/.+)$|$1$2|;' %{el6htcont}/sysconfig/squidguardmgr
%endif
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} install DESTDIR=$RPM_BUILD_ROOT
%{__install} -D -m 0644 doc/squidguardmgr.3 $RPM_BUILD_ROOT%{_mandir}/man8/squidguardmgr.8
%{__install} -d -m 0755 $RPM_BUILD_ROOT%{_localstatedir}/www/squid-gui/
%{__install} -d -m 0700 $RPM_BUILD_ROOT%{_localstatedir}/log/httpd/squidguardmgr/
%{__install} -D -m 0755 %{el6htcont}/rc_squidguardmgr $RPM_BUILD_ROOT%{_initrddir}/squidguardmgr
%{__install} -D -m 0644 %{el6htcont}/squidguardmgr.conf $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf/squidguardmgr.conf
%{__install} -D -m 0644 %{el6htcont}/conf.d/squidguardmgr.cf $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/squidguardmgr.cf
%{__install} -D -m 0644 %{el6htcont}/sysconfig/squidguardmgr $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/squidguardmgr
%{__install} -D -m 0644 %{el6htcont}/logrotate.d/squidguardmgr $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/squidguardmgr

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add squidguardmgr

%preun
/sbin/service squidguardmgr stop &>/dev/null || :
/sbin/chkconfig --del squidguardmgr

%files
%defattr(-,%{squiduid},%{squidgid})
%dir %{_localstatedir}/www/%{wwwdir}
%{_localstatedir}/www/%{wwwdir}/*.cgi
%{_localstatedir}/www/%{wwwdir}/*.conf
%{_localstatedir}/www/%{wwwdir}/*.css
%{_localstatedir}/www/%{wwwdir}/*.js
%attr(4755,root,root) %{_localstatedir}/www/%{wwwdir}/squid_wrapper
%{_localstatedir}/www/%{wwwdir}/images/
%{_localstatedir}/www/%{wwwdir}/lang/
%{_localstatedir}/www/squid-gui/
%defattr(-,root,root)
%dir %{_localstatedir}/log/httpd/squidguardmgr
%config %{_sysconfdir}/httpd/conf/squidguardmgr.conf
%config %{_sysconfdir}/httpd/conf.d/squidguardmgr.cf
%{_initrddir}/squidguardmgr
%{_sysconfdir}/sysconfig/squidguardmgr
%{_sysconfdir}/logrotate.d/squidguardmgr
%doc README INSTALL LICENSE ChangeLog doc/squidguardmgr.pod
%doc %{_mandir}/man8/*

%changelog
* Sun Dec 29 2013 Tatsuya Nonogaki
- initial rpm release (for squidguardmgr-1.13)
