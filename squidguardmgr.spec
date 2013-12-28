%define EL_REL %(UNAMER=$(uname -r); echo ${UNAMER##*.})
%{!?dist:%if %{EL_REL} == "el5"
%define dist .el5
%endif}
Name:           squidguardmgr
Version:        1.13
Release:        1%{?dist}
Summary:        Web GUI for SquidGuard and SquidClamav administration

Group:          Applications/System
License:        GPLv3+
URL:            http://squidguardmgr.darold.net/
Source0:        http://downloads.sourceforge.net/project/%{name}/%{version}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
Vendor:         Gilles Darold <gilles @nospam@ darold.net>
Packager:       Tatsuya Nonogaki <winfield @nospam@ support.email.ne.jp>

BuildRequires:  perl, gcc
BuildRequires:  /usr/bin/squidGuard
Requires:       perl, squid
Requires:       /usr/bin/squidGuard
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
%define wwwdir sgmgr
%define squiduid squid
%define squidgid squid
%{__perl} Makefile.PL CONFFILE=/etc/squid/squidGuard.conf \
DBHOME=/var/squidGuard/blacklists \
LOGDIR=/var/log/squidGuard \
WWWDIR=/var/www/%{wwwdir} \
LANGDIR=en_US \
BASEURL=/squidguardmgr \
SQUIDUSR=%{squiduid} SQUIDGRP=%{squidgid} \
DESTDIR=$RPM_BUILD_ROOT \
QUIET

make

%install
%define el6htcont contrib/EL6/httpd
%if %{EL_REL} == "el5"
%{__perl} -pi.orig -e 's|^(PIDFILE=/var/run)/httpd(/.+)$|$1$2|;' %{el6htcont}/sysconfig/squidguardmgr
%endif
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
%{__install} -D doc/squidguardmgr.3 $RPM_BUILD_ROOT%{_mandir}/man8/squidguardmgr.8
%{__install} -d -m 0755 $RPM_BUILD_ROOT%{_localstatedir}/www/squid-gui/
%{__install} -d -m 0700 $RPM_BUILD_ROOT%{_localstatedir}/log/httpd/squidguardmgr/
%{__install} -D -m 0755 %{el6htcont}/rc_squidguardmgr $RPM_BUILD_ROOT%{_initrddir}/squidguardmgr
%{__install} -D %{el6htcont}/squidguardmgr.conf $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf/squidguardmgr.conf
%{__install} -D %{el6htcont}/conf.d/squidguardmgr.cf $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/squidguardmgr.cf
%{__install} -D %{el6htcont}/sysconfig/squidguardmgr $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/squidguardmgr
%{__install} -D %{el6htcont}/logrotate.d/squidguardmgr $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/squidguardmgr

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add squidguardmgr

%preun
/sbin/service squidguardmgr stop &>/dev/null || :
/sbin/chkconfig --del squidguardmgr

%files
%defattr(644,%{squiduid},%{squidgid},755)
%{_localstatedir}/www/%{wwwdir}/
%attr(755,%{squiduid},%{squidgid}) %{_localstatedir}/www/%{wwwdir}/squidguardmgr.cgi
%attr(4755,root,root) %{_localstatedir}/www/%{wwwdir}/squid_wrapper
%{_localstatedir}/www/squid-gui/
%defattr(-,root,root,700)
%{_localstatedir}/log/httpd/squidguardmgr/
%defattr(644,root,root,-)
%config %{_sysconfdir}/httpd/conf/squidguardmgr.conf
%config %{_sysconfdir}/httpd/conf.d/squidguardmgr.cf
%attr(755,root,root) %{_initrddir}/squidguardmgr
%{_sysconfdir}/sysconfig/squidguardmgr
%{_sysconfdir}/logrotate.d/squidguardmgr
%doc README INSTALL LICENSE ChangeLog doc/squidguardmgr.pod
%doc %{_mandir}/man8/*

%changelog
* Sun Dec 29 2013 Tatsuya Nonogaki
- initial rpm release (for squidguardmgr-1.13)
