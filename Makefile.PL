use ExtUtils::MakeMaker qw(prompt WriteMakefile);

my @ALLOWED_ARGS = ('CONFFILE','DBHOME','CGIDIR','HTMLDIR','DESTDIR','QUIET','LANGDIR','BASEURL','WWWDIR','LOGDIR','SQUIDUSR','SQUIDGRP', 'CICAP_SOCKET','SQUIDCLAMAVCONF');

# Parse command line arguments and store them as environment variables
while ($_ = shift) {
	my ($k,$v) = split(/=/, $_, 2);
	if (grep(/^$k$/, @ALLOWED_ARGS)) {
		$ENV{$k} = $v;
	}
}
$ENV{DESTDIR} =~ s/\/$//;

# Default install path for packaging support.
my $DESTDIR = $ENV{DESTDIR} || '';
$ENV{INSTALLDIRS} ||= 'vendor';
# Default install path
my $CONFFILE = $ENV{CONFFILE} || ''; # SquidGuard configuration file
my $DBHOME = $ENV{DBHOME} || ''; # SquidGuard DB directory
my $LOGDIR = $ENV{LOGDIR} || ''; # SquidGuard logs directory
my $LANGDIR = $ENV{LANGDIR} || 'en_US'; # Default SquidGuard Manager language
# SquidGuard Manager default install base directory
my $WWWDIR = $ENV{WWWDIR} || '/var/www/squidguardmgr';
$WWWDIR .= '/' if ($WWWDIR && ($WWWDIR !~ /\/$/));
# Where to install CGI: $WWWDIR/$CGIDIR. Default: $WWWDIR
my $CGIDIR = $ENV{CGIDIR} || '';
$CGIDIR .= '/' if ($CGIDIR && ($CGIDIR !~ /\/$/));
# Where to install css,js and images files: $WWWDIR/$HTMLDIR. Default: $WWWDIR
my $HTMLDIR = $ENV{HTMLDIR} || '';
$HTMLDIR .= '/' if ($HTMLDIR && ($HTMLDIR !~ /\/$/));
# Base url where css,js and images files will be found. Default: /squidguardmgr
my $BASEURL = $ENV{BASEURL} || '/squidguardmgr';
# Squid running user and group
my $SQUIDUSR = $ENV{SQUIDUSR} || '';
my $SQUIDGRP = $ENV{SQUIDGRP} || '';
my $CICAP_SOCKET = $ENV{CICAP_SOCKET} || '';
my $SQUIDCLAMAVCONF = $ENV{SQUIDCLAMAVCONF} || '';
my $SQUIDCLAMAV = $ENV{SQUIDCLAMAV} || '';
if ($CICAP_SOCKET) {
	$SQUIDCLAMAV = 'c-icap';
}

# Try to find all binary used by SquidGuard Manager
$WWWDIR .= '/' if ($WWWDIR && ($WWWDIR !~ /\/$/));
my $tail = `which tail 2>/dev/null`;
chomp($tail);
if (!$tail) {
	die "NOTICE: This tool requires system command: tail, can't find it in your path\n";
}
my $grep = `which grep 2>/dev/null`;
chomp($grep);
if (!$grep) {
	die "NOTICE: This tool requires the system command: grep, can't find it in your path\n";
}
my $find = `which find 2>/dev/null`;
chomp($find);
if (!$find) {
	die "NOTICE: This tool requires the system command: find, can't find it in your path\n";
}
my $diff = `which diff 2>/dev/null`;
chomp($diff);
if (!$diff) {
	die "NOTICE: This tool requires the system command: diff, can't find it in your path\n";
}
my $rm = `which rm 2>/dev/null`;
chomp($rm);
if (!$rm) {
	die "NOTICE: This tool requires the system command: rm, can't find it in your path\n";
}

# Get the path to squidGuard binary or disable it
my $squidGuard = `which squidGuard 2>/dev/null`;
chomp($squidGuard);
if (!-e $squidGuard) {
	$squidGuard = prompt('Path to squidGuard program?','off');
}
if (!-e $squidGuard && (lc($squidGuard) ne 'off')) {
	die "NOTICE: This tool requires the system command: squidGuard, can't find it in your path\n";
}
my $squidGuardConf = $CONFFILE || '';
if (!$squidGuardConf) {
	foreach ('/usr/local/squidGuard/squidguard.conf','/usr/local/squidGuard/etc/squidguard.conf','/usr/local/etc/squidguard.conf','/etc/squidguard.conf','/etc/squid/squidguard.conf','/etc/squid/squidGuard.conf') {
		$squidGuardConf = $_, last if (-e $_);
	}
	if (lc($squidGuard) eq 'off') {
		$squidGuard = 'off';
	} else {
		if (!-e $squidGuardConf) {
			$squidGuardConf = prompt('Path to squidGuard configuration file?', '');
		}
		if (!-e $squidGuardConf) {
			print "NOTICE: can't find squidguard.conf in your system.\n";
		}
	}
}
if (-e $squidGuardConf && !$DBHOME) {
	my $dbhome = `grep "dbhome" $squidGuardConf`;
	chomp($dbhome);
	if ($dbhome =~ s/^[^\s\t]+[\s\t]+//) {
		$DBHOME = $dbhome;
	}
}
if (-e $squidGuardConf && !$LOGDIR) {
	my $logdir = `grep "logdir" $squidGuardConf`;
	chomp($logdir);
	if ($logdir =~ s/^[^\s\t]+[\s\t]+//) {
		$LOGDIR = $logdir;
	}
}

my $squidclamav = $SQUIDCLAMAV || '';
my $cicapSocket = $CICAP_SOCKET || '';
if (!$cicapSocket && !$squidclamav) {
	$squidclamav = prompt('Do you use c-icap SquidClamav v6.x services?', 'no');
	if ($squidclamav && $squidclamav !~ /^no/i) {
		$squidclamav = 'c-icap';
		# Search for the c-icap command socket
		my $cicapConf = '';
		foreach ('/usr/local/c-icap/etc/c-icap.conf','/usr/local/etc/c-icap.conf','/etc/c-icap/c-icap.conf','/etc/c-icap.conf') {
			$cicapConf = $_, last if (-e $_);
		}
		if (!$cicapConf) {
			$cicapConf = prompt('Path to c-icap configuration file?', '/usr/local/etc/c-icap.conf');
		}
		if (-e $cicapConf) {
			$cicapSocket = `grep "^CommandsSocket" $cicapConf | awk '{print \$2}'`;
			chomp($cicapSocket);
		}
	} else {
		$squidclamav = `which squidclamav 2>/dev/null`;
		chomp($squidclamav);
		if (!-e $squidclamav) {
			$squidclamav = prompt('Path to squidclamav program?', 'off');
			if (!-e $squidclamav && (lc($squidclamav) ne 'off')) {
				die "NOTICE: This tool requires the system command: squidclamav, can't find it in your path\n";
			}
			if (lc($squidclamav) eq 'off') {
				$squidclamav = 'off';
			}
		}
	}
} elsif ($cicapSocket) {
	$squidclamav = 'c-icap';
}
if ( ($squidclamav eq 'off') && ($squidGuard eq 'off')) {
	die "FATAL: you must either have squidGuard or SquidClamav installed!\n";
}

my $squidclamavConf = $SQUIDCLAMAVCONF || '';
if (!$squidclamavConf) {
	foreach ('/usr/local/etc/squidclamav.conf','/etc/squidclamav.conf','/etc/squidclamav/squidclamav.conf') {
		$squidclamavConf = $_, last if (-e $_);
	}
	if (!-e $squidclamavConf && ($squidclamav ne 'off')) {
		$squidclamavConf = prompt('Path to SquidClamav configuration file?', '');
		if (!-e $squidclamavConf) {
			die "NOTICE: can't find squidclamav.conf it in your system\n";
		}
	}
}

my $squid = `which squid 2>/dev/null`;
chomp($squid);
$squid ||= `which squid3 2>/dev/null`;
chomp($squid);
$squid ||= '/usr/local/squid/sbin/squid';
if (!-e $squid) {
	$squid = prompt('Path to squid program?', '');
	if (!-e $squid && (lc($squid) ne 'off')) {
		die "NOTICE: This tool requires the system command: squid, can't find it in your path\n";
	}
}
$squid =~ s/\//\\\//g;
# Change default path to squid binary
`perl -p -i -e 's/#define SQUID_BINARY.*/#define SQUID_BINARY "$squid"/' squid_wrapper/squid_wrapper.c`;


my $squid_user = $SQUIDUSR || `ps auxw | grep "(squid)" | grep -v grep | awk '{print \$1}'`;
chomp($squid_user);
my $squid_group = $SQUIDGRP || $squid_user;

if (!$squid_user) {
	$squid_user = prompt('What is the user (uid) running Squid or SquidGuard?', 'squid');
	my $ret = `id $squid_user 2>/dev/null`;
	chomp($ret);
	if (!$ret) {
		die "NOTICE: SquidGuard Manager must be run as SquidGuard user, uid=$squid_user not found!\n";
	} else {
		if ($ret =~ /uid=(\d+)\(.* gid=(\d+)\(/) {
			$squid_user = $1;
			$squid_group = $2;
		}
	}
	if (!$squid_user) {
		die "NOTICE: SquidGuard Manager must be run as SquidGuard user, not found!\n";
	}
}
if (!$squid_group) {
	my $ret = `id $squid_user 2>/dev/null`;
	chomp($ret);
	if (!$ret) {
		die "NOTICE: SquidGuard Manager must be run as SquidGuard group, not found!\n";
	} else {
		if ($ret =~ /uid=(\d+)\(.* gid=(\d+)\(/) {
			$squid_group = $2;
		}
	}
	if (!$squid_group) {
		die "NOTICE: SquidGuard Manager must be run as SquidGuard group, not found!\n";
	}
}

# Setup ok. generating squidguardmgr.conf config file
unless(open(OUTCFG, ">cgi-bin/squidguardmgr.conf")) {
	print "\nError: can't write config file cgi-bin/squidguardmgr.conf, $!\n";
	exit 0;
}

	print OUTCFG qq{
#
# SquidGuard Manager configuration file
#

# Path to the grep system command
GREP	$grep

# Path to the find system command
FIND	$find

# Path to the tail system command
TAIL	$tail

# Path to the diff system command
DIFF	$diff

# Path to the rm system command
RM	$rm

# Path to the SquidGuard program. You can set it to off to disable the
# SquidGuard manager interface and get only the SquidClamav manager.
SQUIDGUARD	$squidGuard

# Path to the SquidGuard configuration file
CONF_FILE	$squidGuardConf

# Path to the SquidClamav program. You can set it to off to disable the
# SquidClamav manager interface and get only the SquidGuard manager.
# If you use SquidClamav v6.x with the c-icap server, set this directive to
# the value: c-icap
SQUIDCLAMAV	$squidclamav

# Path to the c-icap control socket. Used by SquidClamav Manager to reload
# c-icap server to apply SquidClamav configuration changes. Used only with
# SquidClamav v6.x branch.
C_ICAP_SOCKET	$cicapSocket

# Path to the SquidClamav configuration file
SC_CONF_FILE	$squidclamavConf

# Used to set the language, default is en_US.
# Current translation are: en_US, fr_FR.
LANG		$LANGDIR

# Command to reload Squid. You may use the wrapper as squid
# can only be reload as root. This wrapper will run the command
# /usr/local/squid/sbin/squid -k reconfigure
SQUID_WRAPPER	${WWWDIR}${CGIDIR}squid_wrapper

# SquidGuardMgr URL base where images are stored
IMG_DIR		$BASEURL/images

# SquidGuardMgr Style Sheet CSS URL
CSS_FILE	$BASEURL/squidguardmgr.css

# SquidGuardMgr Javascript URL
JS_FILE		$BASEURL/squidguardmgr.js

# Comma separated list of DNS Blacklists
#DNSBL	your.preferred.blacklist.com,other.preferred.blacklist.com

# Number of last lines displayed from log files
TAIL_LINES	1000

# Keep added/removed items from squidGuard blocklists as diff file
# to be able to recover change after a fresh download of blocklists
KEEP_DIFF       1

};
close(OUTCFG);

unless(open(INST, ">install_all.sh")) {
	print "\nError: can't write post install file install_all.sh, $!\n";
	exit 0;
}
print INST qq{#!/bin/sh
if [ ! -d "$DESTDIR$WWWDIR" ]; then
	mkdir -p $DESTDIR$WWWDIR
fi

if [ -e $DESTDIR$WWWDIR${CGIDIR}squidguardmgr.conf ]; then
	echo "File squidguardmgr.conf already exists. Rename it into squidguardmgr.conf.old"
	mv $DESTDIR$WWWDIR${CGIDIR}squidguardmgr.conf $DESTDIR$WWWDIR${CGIDIR}squidguardmgr.conf.old
fi
};
if ($DBHOME) {
	print INST qq{
perl -p -i -e 's#my \\\$DBHOME.*=.*#my \\\$DBHOME = "$DBHOME";#' cgi-bin/squidguardmgr.cgi
};
}

if ($LOGDIR) {
	print INST qq{
perl -p -i -e 's#my \\\$LOGDIR.*=.*#my \\\$LOGDIR = "$LOGDIR";#' cgi-bin/squidguardmgr.cgi
};
}

print INST qq{
install -m 755 --owner=$squid_user --group=$squid_group cgi-bin/squidguardmgr.cgi $DESTDIR$WWWDIR$CGIDIR
install -m 644 --owner=$squid_user --group=$squid_group cgi-bin/squidguardmgr.conf $DESTDIR$WWWDIR$CGIDIR
cp -rf cgi-bin/lang/ $DESTDIR$WWWDIR$CGIDIR
chown -R $squid_user:$squid_group $DESTDIR$WWWDIR$CGIDIR
install -m 644 --owner=$squid_user --group=$squid_group htdocs/squidguardmgr.css $DESTDIR$WWWDIR$HTMLDIR
install -m 644 --owner=$squid_user --group=$squid_group htdocs/squidguardmgr.js $DESTDIR$WWWDIR$HTMLDIR
cp -rf htdocs/images/ $DESTDIR$WWWDIR$HTMLDIR
chown -R $squid_user:$squid_group $DESTDIR$WWWDIR$HTMLDIR
install -m 755 --owner=0 --group=0 squid_wrapper/squid_wrapper $DESTDIR$WWWDIR$CGIDIR
chmod u+s $DESTDIR$WWWDIR$CGIDIR/squid_wrapper
};
if (!$ENV{QUIET}) {
	print INST qq{
echo "
-----------------------------------------------------------------------------

1. Modify Apache httpd.conf to change the running uid and gid to squid user.
2. Modify your httpd.conf to allow access to CGI scripts like follow:

	Alias /squidguardmgr $WWWDIR$HTMLDIR
	<Directory $WWWDIR$HTMLDIR>
	    Options +ExecCGI
	    AddHandler cgi-script .cgi
	    DirectoryIndex squidguardmgr.cgi
	    Order deny,allow
	    Deny from all
	    Allow from 192.168.1.24
	</Directory>

3. If necessary, set additional grants to Squidguard Manager in httpd.conf.
   Restart and ensure that httpd is running.
4. Browse to http://proxy.host.dom/squidguardmgr/ to ensure that things are
   working properly.
For more information, see http://squidguardmgr.darold.net/.
-----------------------------------------------------------------------------
" | more
};
}
close(INST);

`chmod 755 install_all.sh`;

WriteMakefile(
    'NAME'         => 'squidguardmgr',
    'VERSION_FROM' => 'cgi-bin/squidguardmgr.cgi',
    'dist'         => {
			'COMPRESS'=>'gzip -9f', 'SUFFIX' => 'gz',
			'ZIP'=>'/usr/bin/zip','ZIPFLAGS'=>'-rl'
		      },
    'AUTHOR'       => 'Gilles Darold (gilles@darold.net)',
    'ABSTRACT'     => 'SquidGuard/SquidClamav administration GUI',
    'DESTDIR'      => $ENV{DESTDIR},
    'INSTALLDIRS'  => $ENV{INSTALLDIRS},
    'clean'        => {FILES => "install_all.sh cgi-bin/squidguardmgr.conf squid_wrapper/squid_wrapper"}
);

sub MY::install {
	my $self = shift;

	my $string = $self->MM::install;
	#$string =~ s/(pure_install\s+)(.*)/$1 install_all $2/;
	$string =~ s/pure_install\s+.*/install_all/;

	return $string;
}

sub MY::postamble {
	my $postamble = <<'END';
install_all: install_all.sh squid_wrapper/squid_wrapper.c
	cc -o squid_wrapper/squid_wrapper squid_wrapper/squid_wrapper.c
	sh install_all.sh
END
	return $postamble;
}

if (!$ENV{QUIET}) {
	print "Done...\n\n";
	print "Now type 'make && make install'\n\n";
}

