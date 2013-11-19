#!/usr/bin/perl
#-----------------------------------------------------------------------------
#
# SquidGuard Manager
#
# Manage SquidGuard and SquidClamav BlockLists and configuration file.
#
# Programing language: Perl
# Author: Gilles DAROLD <gilles AT darold DOT net>
# Copyright: 2010-2013 Gilles DAROLD, all rights reserved
# License: GPL v3
#-----------------------------------------------------------------------------
use vars qw($VERSION $AUTHOR $COPYRIGHT $LICENSE);

use strict qw{vars subs};

$VERSION     = '1.12',
$AUTHOR      = 'Gilles DAROLD <gilles AT darold DOT net>';
$COPYRIGHT   = 'Copyright &copy; 2010-2013 Gilles DAROLD, all rights reserved';
$LICENSE     = 'GPL v3';

my $PROGRAM     = 'SquidGuard Manager';
my $SGMGR_SITE  = 'http://squidguardmgr.darold.net/';
my $SC_PROGRAM  = 'SquidClamav Manager';

# Default SquidGuard installation path
my $DBHOME = "/var/lib/squidguard/db";
my $LOGDIR = "/var/log/squid";

# Variables that can be overidden into the squidguardmgr.conf file
our $DIFF       = '/usr/bin/diff';
our $GREP       = '/bin/grep';
our $FIND       = '/usr/bin/find';
our $RM         = '/bin/rm';
our $TAIL       = '/usr/bin/tail';
our $SQUIDGUARD = '/usr/local/bin/squidGuard';
our $BLDESC     = 'description.dat';
our $CONF_FILE  = '/usr/local/squidGuard/squidguard.conf';
our $LANGDIR    = 'lang';
our $LANG       = 'en_US';
our $IMG_DIR    = 'images';
our $CSS_FILE   = 'squidguardmgr.css';
our $JS_FILE    = 'squidguardmgr.js';
our $DNSBL      = '';
our $LOG_LINES  = 1000;
our $SQUIDCLAMAV   = '/usr/bin/squidclamav';
our $SC_CONF_FILE  = '/etc/squidclamav.conf';
our $SQUID_WRAPPER = '/var/www/squidguardmgr/squid_wrapper';
our $C_ICAP_SOCKET = '/var/run/c-icap/c-icap.ctl';
our $KEEP_DIFF  = 1;

# Configuration file
my $SGM_CONF    = 'squidguardmgr.conf';

# Other globals variables

my @SC_GLOBALVAR = ('squid_ip','squid_port','clamd_local','clamd_ip','clamd_port','squidguard','logfile','redirect','maxsize','maxredir','stat','debug','timeout','trust_cache','useragent','logredir','dnslookup');

my @GLOBALVAR = ('logdir','dbhome','ldapbinddn','ldapbindpass','ldapcachetime','ldapprotover','mysqlusername','mysqlpassword','mysqldb');
my @SRC_KEYWORD = ('ip','iplist','ldapipsearch','domain','user','userlist','ldapusersearch','userquery','execuserlist');
my @TIME_KEYWORD = ('weekly','date');

my %SRC_ALIAS = (
	'ip' => 'Ip addresses or range',
	'iplist' => 'File of Ip addresses or range',
	'domain' => 'Domain name',
	'user' => 'Users',
	'userlist' => 'File of users',
	'ldapipsearch' => 'Search ip in LDAP',
	'execuserlist' => 'Program returning user list',
	'ldapusersearch' => 'Search users in LDAP',
	'userquery' => 'Search User in SQL database',
);

my %dayabbr = (
	'Sunday' => 's',
	'Monday' => 'm',
	'Tuesday' => 't',
	'Wednesday' => 'w',
	'Thursday' => 'h',
	'Friday' => 'f',
	'Saturday' => 'a'
);

my %abbrday = (
	's' => 'Sunday',
	'm' => 'Monday',
	't' => 'Tuesday',
	'w' => 'Wednesday',
	'h' => 'Thursday',
	'f' => 'Friday',
	'a' => 'Saturday'
);

use CGI;

my %CONFIG = ();

my $SG_VER       = '';
my $ERROR        = '';
my $CGI = new CGI;
my $ACTION = $CGI->param('action') || '';
my $APPLY = $CGI->param('apply') || '';
my $VIEW = $CGI->param('view') || '';

my $BL   = $CGI->param('blacklist') || '';
my $TIME = $CGI->param('schedule') || '';
my $REW  = $CGI->param('rewrite') || '';
my $SRC  = $CGI->param('source') || '';
my $CAT  = $CGI->param('category') || '';
my $ACL  = $CGI->param('acl') || '';
my $PATH = $CGI->param('path') || '';
my $OLD  = &decode_url($CGI->param('oldvalue')) || '';
$LANG    = $CGI->param('lang') || $LANG;

# Set globals variable following the content of squidguardmgr.conf 
&read_sgm_config();
$ACTION = 'squidclamav' if ($SQUIDGUARD =~ /^(no|off|disable)/i);
my $IMG_LOGO     = "<img src=\"$IMG_DIR/squidguardmgr-logo.png\" align=\"center\" border=\"0\">";
my $IMG_REDIRECT = "<img src=\"$IMG_DIR/redirect.png\" border=\"no\">";
my $IMG_EDIT     = "<img src=\"$IMG_DIR/edit.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_ADD      = "<img src=\"$IMG_DIR/new.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_DELETE   = "<img src=\"$IMG_DIR/trash.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_NODELETE = "<img src=\"$IMG_DIR/notrash.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_REMOVE   = "<img src=\"$IMG_DIR/remove.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_SMALL_REMOVE   = "<img src=\"$IMG_DIR/remove.png\" width=\"10\" height=\"10\" border=\"no\">";
my $IMG_NOREMOVE = "<img src=\"$IMG_DIR/noremove.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_SMALL_NOREMOVE = "<img src=\"$IMG_DIR/noremove.png\" width=\"10\" height=\"10\" border=\"no\">";
my $IMG_NOIP     = "<img src=\"$IMG_DIR/checked.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_REBUILD  = "<img src=\"$IMG_DIR/rebuild.png\" width=\"15\" height=\"15\" border=\"no\">";
my $IMG_LOG      = "<img src=\"$IMG_DIR/log.png\" width=\"15\" height=\"15\" border=\"no\">";

# Get translated strings
my %LANG = &get_translation("$LANGDIR/$LANG");

if (!-x $SQUID_WRAPPER) {
	$SQUID_WRAPPER = '';
}

if ($ACTION eq 'squidclamav') {
	my $error = '';
	if (! -e $SC_CONF_FILE && ($VIEW eq 'init') ) {
		$VIEW = '';
	}

	# Read configuration from file squidclamav.conf
	%CONFIG = &sc_get_configuration() if (-e $SC_CONF_FILE);

	if ($VIEW eq 'showlog') {
		&show_filecontent($PATH, 1);
		exit 0;
	}

	&sc_smgr_header();
	if ($VIEW eq 'squid') {
		if ($SQUID_WRAPPER) {
			print "Running: $SQUID_WRAPPER ... \n";
			$ERROR = `$SQUID_WRAPPER 2>&1`;
			&error($ERROR) if ($ERROR);
			print "Ok." if (!$ERROR);
		}
		$VIEW = '';
	}
	if ($VIEW eq 'cicap') {
		if (-e $C_ICAP_SOCKET) {
			print STDERR "Running: echo -n \"reconfigure\" > $C_ICAP_SOCKET ... \n";
			$ERROR = `echo -n "reconfigure" > $C_ICAP_SOCKET`;
			&error($ERROR) if ($ERROR);
			print "Ok." if (!$ERROR);
		}
		$VIEW = '';
	}

	&error($error) if ($error);
	if (! -e $SC_CONF_FILE) {
		print "<table width=\"100%\"><tr><th style=\"text-align: left;\">";
		print &translate("Configuration file doesn't exists"), ".";
		print "&nbsp;&nbsp;&nbsp;<input type=\"button\" name=\"init\" value=\"", &translate('Create'), "\" onclick=\"document.forms[0].view.value='init'; document.forms[0].submit(); return false;\"></th></tr>\n";
		print "</table>\n";
		&smgr_footer();
		exit 0;
	}

	if ($APPLY && ($VIEW eq 'speed')) {
		# Add default virus scan exclusion fo speed
		$CGI->param('abort1', '^.*\.(css|xml|xsl|js|html|jsp)$');
		$CGI->param('abort2', '^.*\.swf$');
		$CGI->param('abortcontent1', '^image\/.*$');
		$CGI->param('abortcontent2', '^text\/.*$');
		$CGI->param('abortcontent3', '^application\/x-javascript$');
		$CGI->param('abortcontent4', '^video\/.*$');
		$CGI->param('abortcontent5', '^application\/x-shockwave-flash$');
		$VIEW = 'aborts';
	}
	if ($APPLY) {
		&sc_apply_change();
		&sc_save_config();
	}


	# Read configuration from file squidclamav.conf
	%CONFIG = &sc_get_configuration();
	if ($VIEW eq 'globals') {
		&sc_show_globals();
	} elsif ($VIEW eq 'whitelists') {
		&sc_show_whitelist();
	} elsif ($VIEW eq 'trustusers') {
		&sc_show_trustuser();
	} elsif ($VIEW eq 'trustclients') {
		&sc_show_trustclient();
	} elsif ($VIEW eq 'aborts') {
		&sc_show_abort();
	} elsif ($VIEW eq 'dump') {
		&sc_show_config();
	} else {
		print "<table width=\"100%\"><tr><td>\n";
		print &show_help('sc_index');
		print "</td></tr></table>\n";
	}

	&smgr_footer();
	exit 0;
}

if (! -e $CONF_FILE && ($ACTION eq 'init') ) {
	&create_default_config();
}

if (! -e $CONF_FILE) {
	&smgr_header();
	if ($ERROR) {
		&error($ERROR);
	}
	print "<table width=\"100%\"><tr><th style=\"text-align: left;\">";
	print &translate("Configuration file doesn't exists"), ".";
	print "&nbsp;&nbsp;&nbsp;<input type=\"button\" name=\"init\" value=\"", &translate('Create'), "\" onclick=\"document.forms[0].action.value='init'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	&smgr_footer();
	exit 0;
}

# Read configuration from file squidGuard.conf
%CONFIG = &get_configuration();

if ($ACTION eq 'viewlist') {
	&show_listcontent($PATH);
	exit 0;
} elsif (($ACTION eq 'editfile') || ($ACTION eq 'viewfile')) {
	&show_filecontent($PATH, $CGI->param('tail'));
	exit 0;
}

if ( $APPLY && $CGI->param('filelist')) {
	&save_listcontent($CGI->param('filelist'));
	exit 0;
}

if ( $APPLY && $CGI->param('filename')) {
	&save_filecontent($CGI->param('filename'));
	exit 0;
}

&smgr_header();

if ($ACTION eq 'squid') {
	if ($SQUID_WRAPPER) {
		$ERROR = `$SQUID_WRAPPER`;
	}
	$ACTION = '';
}

if ($ACTION eq 'autocreate') {
	&autocreate_filters();
}

if ($BL && ($ACTION eq 'search') ) {
	print "<p style=\"color: black; font-weight: bold;\">", &translate('Search results'), " :</p>";
	print &search_database($CGI->param('search'));
	
	if ($BL eq 'all') {
		$ACTION = 'blacklists';
		$BL = '';
	} else {
		$ACTION = 'bledit';
		$BL =~ s/\/.*//;
	}
}

if ($BL && ($ACTION eq 'bldelete') ) {
	if (-d "$CONFIG{dbhome}/$BL") {
		$BL =~ s/[^a-z0-9\_\-]+//ig;
		`$RM -rf "$CONFIG{dbhome}/$BL"` if ($CONFIG{dbhome} && $BL);
	}
	$ACTION = 'blacklists';
	$BL = '';
}

if ($BL && ($ACTION eq 'rebuild') ) {
	&rebuild_database($BL);
	if ($BL eq 'all') {
		$ACTION = 'blacklists';
		$BL = '';
	} else {
		$ACTION = 'bledit';
		$BL =~ s/\/.*//;
	}
}

# Apply change if any
if ($APPLY && ($ACTION eq 'bledit') ) {
	if ($APPLY eq 'descr') {
		&save_blacklist_description();
	} else {
		&save_blacklist();
	}
} elsif ($APPLY) {
	&apply_change();
	&save_config();
	# Reread configuration from file
	%CONFIG = &get_configuration();
}


if ($ERROR) {
	&error($ERROR);
}

my $valold = &encode_url($OLD);
print qq{
<input type="hidden" name="apply" value="" />
<input type="hidden" name="blacklist" value="$BL" />
<input type="hidden" name="oldvalue" value="$valold" />
};

#if (!$ACTION) {
#	print "<img src=\"$IMG_DIR/squidguardmgr.gif\" align=\"center\" border=\"no\">\n";
#}

if ($ACTION eq 'blacklists') {
	&show_blacklists();
} elsif ($ACTION eq 'globals') {
	&show_globals();
} elsif ($ACTION eq 'sources') {
	&show_sources();
} elsif ($ACTION eq 'sourcesedit') {
	&edit_sources($SRC);
} elsif ($ACTION eq 'rewrites') {
	&show_rewrites();
} elsif ($ACTION eq 'rewritesedit') {
	&edit_rewrites($REW);
} elsif ($ACTION eq 'times') {
	&show_times();
} elsif ($ACTION eq 'timesedit') {
	&edit_times($TIME);
} elsif ( ($ACTION eq 'bledit') && $BL ) {
	&edit_blacklist($BL);
} elsif ($ACTION eq 'categories') {
	&show_categories();
} elsif ($ACTION eq 'categoriesedit') {
	&edit_categories($CAT, $CGI->param('blacklist'));
} elsif ($ACTION eq 'acl') {
	&show_acl();
} elsif ($ACTION eq 'aclsedit') {
	&edit_acls($ACL);
} elsif ($ACTION eq 'dump') {
	&show_config();
} elsif ($ACTION eq 'logs') {
	&show_logs();
} else {
	print "<table width=\"100%\"><tr><td>\n";
	print &show_help('index');
	print "</td></tr></table>\n";
}

&smgr_footer();

exit 0;


#-----------------------------------------------------------------------------

sub normalize_configfile
{

	# First normalize file for better parsing
	if (not open(IN, $CONF_FILE)) {
		$ERROR = "Can't open configuration file $CONF_FILE: $!\n";
		return 0;
	}
	my @txt = <IN>;
	close(IN);
	map { s/
//gs } @txt;
	
	my $content = join('', @txt);
	@txt = ();
	$content =~ s/\n[\s\t]*\{/ \{/gs;
	if (not open(OUT, ">$CONF_FILE")) {
		$ERROR = "Can't write to configuration file $CONF_FILE: $!<br>\n";
		$ERROR .= "File grants: " . `ls -la $CONF_FILE` . "<br>\n";
		my $username = getpwuid( $< );
		$ERROR .= "SquidGuardMgr is running under user: $username\n";
		return 0;
	}
	print OUT $content;
	close(OUT);

	return 1;
}

sub get_configuration
{
	my %infos = ();

	# First normalize file for better parsing
	return if (!&normalize_configfile());
	
	if (not open(IN, $CONF_FILE)) {
		$ERROR = "Can't open configuration file $CONF_FILE: $!\n";
		return;
	}
	my $enter_acl = 0;
	my $cur_src = '';
	my $cur_acl = '';
	my $cur_rew = '';
	my $cur_time = '';
	my $cur_dest = '';
	my $acl_else = '';
	my $src_else = '';
	my $dest_else = '';
	my $rew_else = '';
	while (my $l = <IN>) {
		chomp($l);
		$l =~ s/\#.*//;
		$l =~ s/^[\s\t]+//;
		$acl_else = 0, $src_else = 0, $dest_else = 0, $rew_else = 0 if ($l =~ /\}$/);
		next if ( !$l || ($l eq '}') );
		if ($l =~ /^acl[\s\t]+\{/) {
			$enter_acl = 1;
			$cur_src = '';
			$cur_rew = '';
			$cur_time = '';
			$cur_dest = '';
			next;
		} elsif ($l =~ /^(src|source)[\s\t]+([^\s\t]+)[\s\t]+\{/) {
			$cur_src = $2;
			$enter_acl = 0;
			$cur_rew = '';
			$cur_time = '';
			$cur_dest = '';
			next;
		} elsif ($l =~ /^(rew|rewrite)[\s\t]+([^\s\t]+)[\s\t]+\{/) {
			$cur_rew = $2;
			$enter_acl = 0;
			$cur_src = '';
			$cur_time = '';
			$cur_dest = '';
			next;
		} elsif ($l =~ /^time[\s\t]+([^\s\t]+)[\s\t]+\{/) {
			$cur_time = $1;
			$enter_acl = 0;
			$cur_src = '';
			$cur_rew = '';
			$cur_dest = '';
			next;
		} elsif ($l =~ /^(dest|destination)[\s\t]+([^\s\t]+)[\s\t]+\{/) {
			$cur_dest = $2;
			$cur_time = '';
			$enter_acl = 0;
			$cur_src = '';
			$cur_rew = '';
			next;
		}
		if ($enter_acl && ($l =~ /\belse\b/)) {
			$acl_else = 1;
			next;
		}
		if ($cur_src && ($l =~ /\belse\b/)) {
			$src_else = 1;
			next;
		}
		if ($cur_dest && ($l =~ /\belse\b/)) {
			$dest_else = 1;
			next;
		}
		if ($cur_rew && ($l =~ /\belse\b/)) {
			$rew_else = 1;
			next;
		}
		if ($enter_acl && ($l =~ /^([^\s\t]+)[\s\t]+(outside|within)[\s\t]+([^\s\t]+)[\s\t]+\{/) ) {
			$cur_acl = $1;
			$infos{acl}{$cur_acl}{'extended'}{$2} = $3;
		} elsif ($enter_acl && ($l =~ /^([^\s\t]+)[\s\t]+\{/) ) {
			$cur_acl = $1;
		}

		my ($k, $v) = split(/[\t\s]+/, $l, 2);

		# replace synonyme
		if ( ($cur_dest || $cur_src || $cur_rew) && ($k eq 'logfile')) {
			$k = 'log';
		}

		# parse global definition
		if (grep(/^\Q$k\E$/, @GLOBALVAR)) {
			$infos{$k} = $v;
			next;
		}
		# Parse categories defintions
		if ($cur_dest) {
			if (!$dest_else) {
				$infos{dest}{$cur_dest}{$k} = $v;
			} else {
				$infos{dest}{$cur_dest}{else}{$k} = $v;
			}
			next;
		}
		# Parse rewrite rules
		if ($cur_rew) {
			if ($k eq 'log') {
				if (!$rew_else) {
					$infos{rew}{$cur_rew}{$k} = $v;
				} else {
					$infos{rew}{$cur_rew}{else}{$k} = $v;
				}
			} elsif ($k =~ /(within|outside)/) {
				$infos{rew}{$cur_rew}{$k} = $v;
			} else {
				if (!$rew_else) {
					push(@{$infos{rew}{$cur_rew}{rewrite}}, $k);
				} else {
					push(@{$infos{rew}{$cur_rew}{else}{rewrite}}, $k);
				}
			}
			next;
		}
		# Parse source definitions
		if ($cur_src && grep(/^$k$/, @SRC_KEYWORD)) {
			if (!$src_else) {
				push(@{$infos{src}{$cur_src}{$k}}, $v);
			} else {
				push(@{$infos{src}{$cur_src}{else}{$k}}, $v);
			}
			next;
		} elsif ($cur_src) {
			if (!$src_else) {
				$infos{src}{$cur_src}{$k} = $v;
			} else {
				$infos{src}{$cur_src}{else}{$k} = $v;
			}
			next;
		}
		# Parse time rules
		if ($cur_time && grep(/^$k$/, @TIME_KEYWORD)) {
			$v =~ s/(\d+)[\s\t]+\-[\s\t]+(\d+)/$1\-$2/g;
			my @datas = split(/[\s\t]+/, $v);
			my $hours = '';
			if ($datas[-1] =~ /\d+:\d+\-\d+:\d+/) {
				$hours = pop(@datas);
			}
			my $days = '';
			if (($k eq 'weekly') && ($#datas > 0)) {
				foreach my $d (@datas) {
					if (length($d) > 1) {
						my $s = grep(/^$d/, keys %dayabbr);
						$days .= $dayabbr{$s};
					} else {
						$days .= $d;
					}
				}
			} elsif ($k eq 'weekly') {
				$days = $datas[0];
			} elsif ($k eq 'date') {
				$days = join(' ', @datas);
			}
			push(@{$infos{time}{$cur_time}{days}}, "$days|$hours");
		}
		# Parse ACL definitions
		if ($cur_acl) {
			if (!$acl_else) {
				if ($l =~ /^pass[\s\t]+(.*)/) {
					push(@{$infos{acl}{$cur_acl}{'pass'}}, split(/[\s\t]+/, $1));
				}
				if ($l =~ /^redirect[\s\t]+(.*)/) {
					$infos{acl}{$cur_acl}{'redirect'} = $1;
				}
				if ($l =~ /^(rew|rewrite)[\s\t]+(.*)/) {
					push(@{$infos{acl}{$cur_acl}{'rewrite'}}, $2);
				}
			} else {
				if ($l =~ /^pass[\s\t]+(.*)/) {
					push(@{$infos{acl}{$cur_acl}{else}{'pass'}}, split(/[\s\t]+/, $1));
				}
				if ($l =~ /^redirect[\s\t]+(.*)/) {
					$infos{acl}{$cur_acl}{else}{'redirect'} = $1;
				}
				if ($l =~ /^rewrite[\s\t]+(.*)/) {
					push(@{$infos{acl}{$cur_acl}{else}{'rewrite'}}, $1);
				}
			}
		}
	}
	close(IN);

	# Set default values
	$infos{logdir} = $LOGDIR if (!exists $infos{logdir});
	$infos{dbhome} = $DBHOME if (!exists $infos{dbhome});

	return %infos;

}

sub smgr_header
{

	print $CGI->header();
	print $CGI->start_html(
		-title  => "$PROGRAM v$VERSION",
		-author => "$AUTHOR",
		-meta   => { 'copyright' => $COPYRIGHT },
		-style  => { -src => $CSS_FILE },
		-script  => { -src => $JS_FILE },
	);
	my $version = &squidguard_version();
	if ($version =~ /SquidGuard: (\d+\.\d+)/) {
		$SG_VER = $1;
	}
	print $CGI->start_form();
	print "<input type=\"hidden\" name=\"action\" value=\"$ACTION\" />\n";
	print "<input type=\"hidden\" name=\"lang\" value=\"$LANG\" />\n";
	print "<table width=\"100%\" class=\"header\"><tr><td class=\"header\"><a href=\"\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}'; return false;\">$IMG_LOGO</a></td><td class=\"header\">\n<hr>\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='globals'; document.forms[0].submit(); return false;\">", &translate('Globals'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='times'; document.forms[0].submit(); return false;\">", &translate('Schedules'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='sources'; document.forms[0].submit(); return false;\">", &translate('Sources'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='rewrites'; document.forms[0].submit(); return false;\">", &translate('Url rewriting'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='categories'; document.forms[0].blacklist.value=''; document.forms[0].submit(); return false;\">", &translate('Filters'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='acl'; document.forms[0].submit(); return false;\">", &translate('ACLs'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='blacklists'; document.forms[0].submit(); return false;\">", &translate('Manage Lists'), "</a> |\n";
	print "<br><hr>\n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='dump'; document.forms[0].submit(); return false;\">", &translate('View Configuration'), "</a> | \n";
	print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='logs'; document.forms[0].submit(); return false;\">", &translate('View logs'), "</a> |\n";
	if ($SQUIDCLAMAV && (lc($SQUIDCLAMAV) ne 'off')) {
		print "<a href=\"\" onclick=\"window.open('$ENV{SCRIPT_NAME}?action=squidclamav&view=&lang=$LANG','squidclamav','scrollbars=yes,status=no,toolbar=no,width=900,height=800,resizable=yes,screenX=1,screenY=1,top=1,left=1'); return false;\" target=\"_new\">", &translate('SquidClamav'), "</a> |\n";
	}
	if ($SQUID_WRAPPER) {
		print "<a href=\"\" onclick=\"document.forms[0].oldvalue.value=''; document.forms[0].action.value='squid'; document.forms[0].submit(); return false;\">", &translate('Restart Squid'), "</a> |\n";
	}
	print "<hr>\n";
	print "</td></tr></table>\n";

}

sub smgr_footer
{
	print $CGI->end_form();
	print "<p>&nbsp;</p>\n";
	my $version = &squidguard_version();
	if ($SQUIDCLAMAV) {
		$version .= '<br>' . &squidclamav_version();
	}

	print "<table width=\"100%\"><tr><th>$version</th></tr></table>\n" if ($ACTION eq '');
	print "<hr>\n<a href=\"$SGMGR_SITE\" target=\"_new\">$PROGRAM</a> v$VERSION - $COPYRIGHT - License: $LICENSE\n";
	print $CGI->end_html();
}

sub get_blacklists
{
	my $ldir = shift;

	$ldir = '/' . $ldir if ($ldir);
	if (not opendir(DIR, "$CONFIG{dbhome}$ldir")) {
		$ERROR = "Can't open blacklist directory $CONFIG{dbhome}$ldir: $!\n";
		return;
	}
	my @dirs = grep { !/^\..*$/ && -d "$CONFIG{dbhome}$ldir/$_" && !-l "$CONFIG{dbhome}$ldir/$_" } readdir(DIR);
	closedir(DIR);
	# search for subdirectories
	foreach my $d (@dirs) {
		my @tmpdirs = &get_blacklists("$ldir/$d");
		map { s/^/$d\//; } @tmpdirs;
		push(@dirs, @tmpdirs);
	}

	return sort @dirs;
}

sub get_blacklists_description
{

	my %infos = ();

	if (open(IN, "$LANGDIR/$LANG/$BLDESC")) {
		while (<IN>) {
			chomp;
			my ($k, $a, $v) = split(/\t+/);
			$infos{$k}{alias} = $a if ($v);
			$infos{$k}{description} = $v || $a;
		}
		close(IN);
	}

	return %infos;
}

sub show_blacklists
{

	print "<h2>", &translate('Lists management'), "</h2>\n";
	my %blinfo = &get_blacklists_description();
	my @bl = &get_blacklists();
	my $i = 0;
	print "<table width=\"100%\">\n";
	foreach ($i = 0; $i <= $#bl; $i++) {
		if (($i % 10) == 0) {
			print "<tr>\n";
		}
		my $in_use = &acl_in_use($bl[$i]);
		print "<td align=\"left\" title=\"$blinfo{$bl[$i]}{description}\"><a href=\"\" onclick=\"document.forms[0].action.value='bledit'; document.forms[0].blacklist.value='$bl[$i]'; document.forms[0].submit(); return false;\" style=\"font-weight: normal;\">", ($blinfo{$bl[$i]}{alias} || $bl[$i]), "</a>";
		print "<a href=\"\" onclick=\"if (confirm('WARNING: ", &translate('This will remove the list from your system.'), &translate('Are you sure to continue?'), "')) { document.forms[0].action.value='bldelete'; document.forms[0].blacklist.value='$bl[$i]'; document.forms[0].submit(); } return false;\" title=\"", &translate('Remove'), "\">$IMG_SMALL_REMOVE</a>" if (!$in_use);
		print "<font title=\"", &translate('still in use'), "\">$IMG_SMALL_NOREMOVE</font>" if ($in_use);
		print "</td>\n";
		if ($i =~ /9$/) {
			print "</tr>\n";
		}
	}
	print "<tr>\n" if ($i !~ /9$/);
	print "</table>\n";
	print "<table width=\"100%\">\n";
	print "<tr><th style=\"text-align:left;\"><input type=\"text\" name=\"search\" value=\"\" size=\"50\" maxlength=\"128\"> <input type=\"button\" name=\"dosearch\" value=\"", &translate('Search'), "\" onclick=\"document.forms[0].action.value='search'; document.forms[0].blacklist.value='all'; document.forms[0].submit(); return false;\"></th><th style=\"text-align: center;\"><input type=\"button\" name=\"create\" value=\"", &translate('Create a list'), "\" onclick=\"var bl = prompt('", &translate('Enter the new list name'), "'); if (bl != undefined) { document.forms[0].action.value='categoriesedit'; document.forms[0].blacklist.value=bl; document.forms[0].submit(); } return false;\"></th><th style=\"text-align: right;\"><input type=\"button\" name=\"rebuild\" value=\"", &translate('Rebuild all databases'), "\" onclick=\"document.forms[0].action.value='rebuild'; document.forms[0].blacklist.value='all'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print &show_help('blacklists');

}

sub show_globals
{
	print "<h2>", &translate('Globals configuration'), "</h2>\n";
	print "<table align=\"center\" width=\"100%\"><tr><td>\n";
	print "<table align=\"center\">\n";
	print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('Mandatory parameters'), "</b></td></tr>\n";
	print "<tr><th align=\"left\">", &translate('Log directory'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"logdir\" value=\"$CONFIG{logdir}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Databases home'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"dbhome\" value=\"$CONFIG{dbhome}\"/></th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	if ($SG_VER >= 1.4) {
		print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('Retrieving users from MySQL'), "</b></td></tr>\n";
		print "<tr><th align=\"left\">", &translate('MySQL Database'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"mysqldb\" value=\"$CONFIG{mysqldb}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('MySQL Username'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"mysqlusername\" value=\"$CONFIG{mysqlusername}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('MySQL Password'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"mysqlpassword\" value=\"$CONFIG{mysqlpassword}\"/></th></tr>\n";
		print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	}
	if ($SG_VER >= 1.5) {
		print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('Retrieving users from LDAP'), "</b></td></tr>\n";
		print "<tr><th align=\"left\">", &translate('LDAP Bind dn'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"ldapbinddn\" value=\"$CONFIG{ldapbinddn}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('LDAP Password'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"ldapbindpass\" value=\"$CONFIG{ldapbindpass}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('LDAP Protocol (2 or 3)'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"ldapprotover\" value=\"$CONFIG{ldapprotover}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('LDAP Cache time'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"ldapcachetime\" value=\"$CONFIG{ldapcachetime}\"/></th></tr>\n";
		print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	}
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print "</td><td>\n";
	print &show_help('globals');
	print "</td></tr></table>\n";

}

sub edit_blacklist
{
	my $bl = shift;

	my %blinfo = &get_blacklists_description();
	print "<h2>", &translate('List'), ": ", ($blinfo{$bl}{alias} || $bl), "</h2>\n";
	print "<table><tr><td>", &translate('Alias'), ":</td><td colspan=\"2\"><input type=\"text\" name=\"alias\" value=\"$blinfo{$bl}{alias}\" size=\"30\"></td></tr>\n";
	print "<tr><td>", &translate('Description'), ":</td><td><input type=\"text\" name=\"description\" value=\"$blinfo{$bl}{description}\" size=\"60\"></td><th><input type=\"button\" name=\"modify\" value=\"", &translate('Modify'), "\" onclick=\"document.forms[0].action.value='bledit'; document.forms[0].apply.value='descr'; document.forms[0].submit(); return false;\"></th></tr></table>\n";
	print "<input type=\"hidden\" name=\"path\" value=\"\">\n";
	print "<table width=\"100%\"><tr><td>\n";
	print "<table>\n";
	foreach ('domains', 'urls', 'expressions') {
		print "<tr><th align=\"right\">", &translate(ucfirst($_)), "<br><a href=\"\" onclick=\"window.open('$ENV{SCRIPT_NAME}?action=viewlist&path=$bl/$_&lang=$LANG','blwin','scrollbars=yes,status=no,toolbar=no,width=400,height=800,resizable=yes,screenX=1,screenY=1,top=1,left=1'); return false;\" target=\"_new\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a>&nbsp;&nbsp;<a href=\"\" onclick=\"document.forms[0].action.value='rebuild'; document.forms[0].blacklist.value='$bl/$_'; document.forms[0].submit(); return false;\" title=\"", &translate('Rebuild database'), "\">$IMG_REBUILD</a></th><th align=\"left\"><textarea name=\"${bl}_$_\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th></tr>\n";
	}
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"remove\" value=\"", &translate('Remove'), "\" onclick=\"document.forms[0].action.value='bledit'; document.forms[0].apply.value='remove'; document.forms[0].submit(); return false;\">&nbsp;&nbsp;<input type=\"button\" name=\"add\" value=\"", &translate('Add'), "\" onclick=\"document.forms[0].action.value='bledit'; document.forms[0].apply.value='add'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print "</td><td>\n";
	print &show_help('bledit');
	print "</td></tr></table>\n";


}

sub save_blacklist
{
	my $bl = $CGI->param('blacklist') || '';
	my $action = $CGI->param('apply') || '';

	my $domains = '';
	my $expressions = '';
	my $urls = '';

	foreach my $p ($CGI->param()) {
		if ($p =~ /^${bl}_domains/) {
			$domains = $CGI->param($p) || '';
		} elsif ($p =~ /^${bl}_urls/) {
			$urls = $CGI->param($p) || '';
		} elsif ($p =~ /^${bl}_expressions/) {
			$expressions = $CGI->param($p) || '';
		}
	}
	$domains =~ s/
//gs;
	if ($domains) {
		if ($action eq 'add') {
			&add_item("$CONFIG{dbhome}/$bl/domains", split(/[\s\n]+/s, $domains) );
		} elsif ($action eq 'remove') {
			&remove_item("$CONFIG{dbhome}/$bl/domains", split(/[\s\n]+/s, $domains) );
		}
	}
	$urls =~ s/
//gs;
	if ($urls) {
		if ($action eq 'add') {
			&add_item("$CONFIG{dbhome}/$bl/urls", split(/[\s\n]+/s, $urls) );
		} elsif ($action eq 'remove') {
			&remove_item("$CONFIG{dbhome}/$bl/urls", split(/[\s\n]+/s, $urls) );
		}
	}
	$expressions =~ s/
//gs;
	if ($expressions) {
		if ($action eq 'add') {
			&add_item("$CONFIG{dbhome}/$bl/expressions", split(/[\s\n]+/s, $expressions) );
		} elsif ($action eq 'remove') {
			&remove_item("$CONFIG{dbhome}/$bl/expressions", split(/[\s\n]+/s, $expressions) );
		}
	}
}

sub add_item
{
	my ($file, @items) = @_;

	my @exists = ();
	map { $_ =~ s/
//; } @items;
	if (-e "$file") {
		if (open(IN, "$file")) {
			while (my $l = <IN>) {
				chomp($l);
				$l =~ s/
//;
				next if (!$l);
				# check if item already exists
				if (grep($_ eq $l, @items)) {
					push(@exists, $l);
					print "WARNING: $l already exists into $file<br>\n";
				}
			}
			close(IN);
		} else {
			&error("Can't open $file for reading: $!");
			return;
		}
	}
	return if ($#exists == $#items);

	my @add = ();
	foreach my $i (@items) {
		push(@add, $i) if (!grep($i eq $_, @exists));
	}
	if (open(OUT, ">>$file")) {
		print OUT join("\n", @add), "\n";
		close OUT;
		if ($KEEP_DIFF) {
			# Store these items into a squidGuard diff history file
			&add_hist_item("$file.diff.hist", '+', @add);
		}
	} else {
		&error("Can't open $file for writing: $!");
	}
	if (-e "$file.db") {
		# Now load these items dynamically into squidGuard
		if (open(OUT, ">$file.tmpdiff")) {
			map { s/^/\+/; } @add;
			print OUT join("\n", @add), "\n";
			close OUT;
			print `$SQUIDGUARD -u $file.tmpdiff`;
			unlink("$file.tmpdiff");
		} else {
			&error("Can't open $file.tmpdiff for writing: $!<br>");
		}
	} else {
		$file =~ s#$CONFIG{dbhome}/##;
		&rebuild_database($file);
	}
}

sub remove_item
{
	my ($file, @items) = @_;

	if (! -e "$file") {
		print "WARNING: can't remove item from $file, file doesn't exists<br>\n";
		return;
	}

	my @removed = ();
	my $txt = '';
	map { $_ =~ s/
//; } @items;
	if (open(IN, "$file")) {
		while (my $l = <IN>) {
			chomp($l);
			$l =~ s/
//;
			next if (!$l);
			# check if item exists
			if (grep($_ eq $l, @items)) {
				push(@removed, $l);
			} else {
				$txt .= "$l\n";
			}
		}
		close(IN);
	} else {
		&error("Can't open $file for reading: $!");
		return;
	}
	if ($#removed >= 0) {
		if ($txt) {
			if (open(OUT, ">$file")) {
				print OUT "$txt";
				close OUT;
				# Store these items into a squidGuard diff history file
				if ($KEEP_DIFF) {
					&add_hist_item("$file.diff.hist", '-', @removed);
				}
			} else {
				&error("Can't open $file for writing: $!");
			}
		} else {
			# Store these items into a squidGuard diff history file
			if ($KEEP_DIFF) {
				&add_hist_item("$file.diff.hist", '-', @removed);
			}
			unlink($file);
		}
		if (-e "$file.db") {
			# Now load these items dynamically into squidGuard
			if (open(OUT, ">$file.tmpdiff")) {
				map { s/^/\-/; } @removed;
				print OUT join("\n", @removed), "\n";
				close OUT;
				print `$SQUIDGUARD -u $file.tmpdiff`;
				unlink("$file.tmpdiff");
			} else {
				&error("Can't open $file.tmpdiff for writing: $!");
			}
		} else {
			$file =~ s#$CONFIG{dbhome}/##;
			&rebuild_database($file);
		}
	} else {
		print "WARNING: remove patterns not found in file $file<br>\n";
	}

}

sub add_hist_item
{
	my ($file, $prefix, @items) = @_;

	my @exists = ();
	map { $_ =~ s/
//; } @items;
	if (-e "$file") {
		if (open(IN, "$file")) {
			while (my $l = <IN>) {
				chomp($l);
				$l =~ s/
//;
				next if (!$l);
				# check if item already exists
				if (grep($_ eq $l, @items)) {
					push(@exists, $l);
					print "WARNING: $l already exists into $file<br>\n";
				}
			}
			close(IN);
		} else {
			&error("Can't open $file for reading: $!");
			return;
		}
	}
	return if ($#exists == $#items);

	my @add = ();
	foreach my $i (@items) {
		push(@add, $i) if (!grep($i eq $_, @exists));
	}
	if (open(OUT, ">>$file")) {
		map { s/^/$prefix/ } @add;
		print OUT join("\n", @add), "\n";
		close OUT;
	} else {
		&error("Can't open $file for writing: $!");
	}
}

sub show_times
{

	print "<h2>", &translate('Schedules Configuration'), "</h2>\n";
	print "<input type=\"hidden\" name=\"schedule\" value=\"\" />\n";
	print "<table align=\"center\" width=\"80%\">\n";
	print "<tr><th align=\"left\">", &translate('Rule name'), "</th><th align=\"left\">", &translate('Start time'), "</th><th align=\"left\">", &translate('End time'), "</th><th align=\"left\">", &translate('Days'), "</th><th colspan=\"2\">", &translate('Action'), "</th></tr>\n";
	print "<tr><td style=\"border: none;\" colspan=\"6\"><hr></td></tr>\n";
	foreach my $k (sort keys %{$CONFIG{time}}) {
		# Do not activate Delete if this rule is in used
		my $delete = 1;
		foreach my $z (keys %{$CONFIG{src}}) {
			foreach my $e (keys %{$CONFIG{src}{$z}}) {
				if ($CONFIG{src}{$z}{$e} eq $k) {
					$delete = 0;
					last;
				}
			}
			last if (!$delete);
		}
		foreach my $z (keys %{$CONFIG{acl}}) {
			last if (!$delete);
			foreach my $e (keys %{$CONFIG{acl}{$z}{extended}}) {
				if ($CONFIG{acl}{$z}{extended}{$e} eq $k) {
					$delete = 0;
					last;
				}
			}
			last if (!$delete);
		}
		my $i = 0;
		print "<tr><th align=\"left\">$k</th><th colspan=\"3\">&nbsp;</th><th><a href=\"\" onclick=\"document.forms[0].schedule.value='$k'; document.forms[0].action.value='timesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
		if ($delete) {
			print "<th><a href=\"\" onclick=\"document.forms[0].schedule.value='$k'; document.forms[0].action.value='timesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove all'), "\">$IMG_REMOVE</a></th>";
		} else {
			print "<th title=\"", &translate('Still in use'), "\">$IMG_NOREMOVE</th>";
		}
		print "</tr>\n";
		foreach my $val (@{$CONFIG{time}{$k}{days}}) {
			my ($days, $hours) = split(/\|/, $val);
			my ($start,$end) = split(/\-/, $hours);
			my $show_days = '';
			if ($days !~ /\./) {
				while ($days =~ s/^([a-z])//) {
					$show_days .= &translate($abbrday{$1}) . " ";
				}
				$show_days = &translate('Everyday') if ($days eq '*');
			} else {
				$show_days = $days;
			}
			print "<tr><th>&nbsp;</th><td align=\"center\">$start</td><td>$end</td><td>$show_days</td><th><a href=\"\" onclick=\"document.forms[0].schedule.value='$k';document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='timesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
			if ($delete) {
				print "<th><a href=\"\" onclick=\"document.forms[0].schedule.value='$k';document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='timesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
			} else {
				print "<th title=\"", &translate('Still in use'), "\">$IMG_NODELETE</th>";
			}
			print "</tr>\n";
			$i++;
		}
		print "<tr><td style=\"border: none;\" colspan=\"6\"><hr></td></tr>\n";
	}
	print "<tr><th colspan=\"6\" align=\"right\"><input type=\"button\" name=\"new\" value=\"", &translate('New Schedule'), "\" onclick=\"document.forms[0].schedule.value=''; document.forms[0].action.value='timesedit'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub edit_times
{
	my ($name) = &normalyze(shift);

	print "<h2>", &translate('Schedule Edition'), "</h2>\n";

	my $starth = '';
	my $startm = '';
	my $endh = '';
	my $endm = '';
	my $days = '';
	my $hours = '';
	if ( $OLD ne '') {
		my $val = $OLD;
		($days, $hours) = split(/\|/, $val);
		my ($start,$end) = split(/\-/, $hours);
		($starth,$startm) = split(/:/, $start);
		($endh,$endm) = split(/:/, $end);
	}
	print "<table align=\"center\" width=\"100%\"><tr><td>\n";
	print "<table align=\"center\">\n";
	if (!$name) {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"text\" size=\"20\" name=\"time\" value=\"\" /></td></tr>\n";
	} else {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"hidden\" name=\"time\" value=\"$name\" />$name</th></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Start time'), "</th><th align=\"left\">", &translate('End time'), "</th></tr>\n";
	print "<tr><td nowrap=\"1\"><b>", &translate('From'), "</b> <select name=\"starthour\">\n";
	print "<option value=\"\">--</option>\n";
	foreach my $h ("00" .. "23") {
		my $sel = '';
		$sel = 'selected="1" ' if ($h eq "$starth");
		print "<option value=\"$h\" $sel>$h</option>\n";
	}
	print "</select> ", &translate('Hours');
	print " <select name=\"startmin\">\n";
	print "<option value=\"\">--</option>\n";
	foreach my $h ("00", "15", "30", "45") {
		my $sel = '';
		$sel = 'selected="1" ' if ($h eq "$startm");
		print "<option value=\"$h\" $sel>$h</option>\n";
	}
	print "</select> ", &translate('Minutes'), "</td>";

	print "<td nowrap=\"1\"><b>", &translate('To'), "</b> <select name=\"endhour\">\n";
	print "<option value=\"\">--</option>\n";
	foreach my $h ("00" .. "23") {
		my $sel = '';
		$sel = 'selected="1" ' if ($h eq "$endh");
		print "<option value=\"$h\" $sel>$h</option>\n";
	}
	print "</select> ", &translate('Hours');

	print " <select name=\"endmin\">\n";
	print "<option value=\"\">--</option>\n";
	foreach my $h ("00", "15", "30", "45") {
		my $sel = '';
		$sel = 'selected="1" ' if ($h eq "$endm");
		print "<option value=\"$h\" $sel>$h</option>\n";
	}
	print "</select> ", &translate('Minutes'), "</td></tr>";
	print "<tr><th colspan=\"2\">&nbsp;</th></tr>\n";
	print "<tr><th align=\"left\" colspan=\"2\">", &translate('Following week days'), "</th></tr>\n";
	print "<td colspan=\"2\" nowrap=\"1\">\n";
	foreach my $d ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') {
		my $sel = '';
		if ($days !~ /\-/) {
			$sel = 'checked="1" ' if ( ($days =~ /$dayabbr{$d}/) || ($days eq '*'));
		}
		print "<input type=\"checkbox\" name=\"week\" value=\"$dayabbr{$d}\" $sel/>", &translate($d), "\n";
	}
	if ($days !~ /\-/) {
		$days = '';
	}
	print "</td></tr>\n";
	print "<tr><th colspan=\"2\">&nbsp;</th></tr>\n";
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	print "<tr><th align=\"left\" colspan=\"2\">", &translate('Space separated list of date'), "</th></tr>\n";
	print "<tr><td colspan=\"2\">(Format: yyyy.mm.dd yyyy.mm.dd yyyy.mm.dd-yyyy.mm.dd *.mm.dd *.*.dd *.mm.*)</td></tr>\n";
	print "<td colspan=\"2\" nowrap=\"1\">\n";
	print "<input type=\"text\" size=\"80\" name=\"date\" value=\"$days\" />\n";
	print "</td></tr>\n";
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"if (validate_schedule() == true) { document.forms[0].apply.value='1'; document.forms[0].submit();} return false;\"></th></tr>\n";
	print "</table>\n";
	print "</td><td>\n";
	print &show_help('schedules');
	print "</td></tr></table>\n";

}

sub show_rewrites
{
	print "<h2>", &translate('Url rewriting Configuration'), "</h2>\n";
	print "<input type=\"hidden\" name=\"rewrite\" value=\"\" />\n";
	print "<table align=\"center\" width=\"80%\">\n";
	print "<tr><th align=\"left\">", &translate('Rule name'), "</th><th align=\"left\">", &translate('Pattern matching'), "</th><th align=\"left\">", &translate('Substitution'), "</th><th>", &translate('Rewrite options'), "</th><th colspan=\"2\">", &translate('Action'), "</th></tr>\n";
	print "<tr><td style=\"border: none;\" colspan=\"6\"><hr></td></tr>\n";
	foreach my $k (sort keys %{$CONFIG{rew}}) {
		my $delete = 1;
		foreach my $z (keys %{$CONFIG{acl}}) {
			foreach my $e (@{$CONFIG{acl}{$z}{rewrite}}) {
				if ($e eq $k) {
					$delete = 0;
					last;
				}
			}
			last if (!$delete);
		}
		print "<tr><th align=\"left\">$k</th><th colspan=\"3\">&nbsp;</th><th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k'; document.forms[0].oldvalue.value=''; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
		if ($delete) {
			print "<th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k'; document.forms[0].oldvalue.value=''; document.forms[0].action.value='rewritesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove all'), "\">$IMG_REMOVE</a></th>\n";
		} else {
			print "<th title=\"", &translate('Still in use'), "\">$IMG_NOREMOVE</th>\n";
		}
		print "</tr>\n";
		foreach my $val (@{$CONFIG{rew}{$k}{rewrite}}) {
			my ($null, $pattern, $substitute, $opt) = split(/\@/, $val);
			my $options = '';
			$options = &translate('Insensitive') if ($opt =~ /i/);
			$options .= ' / ' if ($opt && ($opt =~ /r/));
			$options .= &translate('Temporary') if ($opt =~ /r/);
			$options .= ' / ' if ($opt && ($opt =~ /R/));
			$options .= &translate('Permanently') if ($opt =~ /R/);
			print "<tr><th>&nbsp;</th><td align=\"center\"><b>", &translate('Replace'), "</b> $pattern</td><td><b>", &translate('with'), "</b> $substitute</td><td>$options</td><th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k'; document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
			print "<th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k'; document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='rewritesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</th>";
			print "</tr>\n";
		}
		&show_log_schedule('rew', 'rewrite', $k, 3);

		if ($CONFIG{rew}{$k}{outside} || $CONFIG{rew}{$k}{within}) {
			print "<tr><th>", &translate('if schedule not match'), "</th><th colspan=\"3\">&nbsp;</th><th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
			print "<th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].action.value='rewritesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove all'), "\">$IMG_REMOVE</a></th></tr>\n";
			foreach my $val (@{$CONFIG{rew}{$k}{else}{rewrite}}) {
				my ($null, $pattern, $substitute, $opt) = split(/\@/, $val);
				my $options = '';
				$options = &translate('Insensitive') if ($opt =~ /i/);
				$options .= ' / ' if ($opt && ($opt =~ /r/));
				$options .= &translate('Temporary') if ($opt =~ /r/);
				$options .= ' / ' if ($opt && ($opt =~ /R/));
				$options .= &translate('Permanently') if ($opt =~ /R/);
				print "<tr><th>&nbsp;</th><td align=\"center\"><b>", &translate('Replace'), "</b> $pattern</td><td><b>", &translate('with'), "</b> $substitute</td><td>$options</td><th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
				print "<th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url($val), "'; document.forms[0].action.value='rewritesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</th>";
 				print "</tr>\n";
			}
			my $v = $CONFIG{rew}{$k}{else}{log} || '';
			my $anon = '';
			if ($v =~ s/anonymous[\s\t]+(.*)/$1/) {
				$anon = "(" . &translate('anonymized') . ")";
			}
			if ($v) {
				print "<tr><th>&nbsp;</th><td colspan=\"3\"><b>", &translate('Log file'), "</b> : ";
			} else {
				print "<tr><th>&nbsp;</th><td colspan=\"3\"><b>", &translate('No log file'), "</b>";
			}
			print "$v $anon";
			print "</td><th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{rew}{$k}{else}{log}"), "'; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
			print "<th><a href=\"\" onclick=\"document.forms[0].rewrite.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{rew}{$k}{else}{log}"), "'; document.forms[0].action.value='rewritesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
			print "</tr>\n";
		}
		print "<tr><td style=\"border: none;\" colspan=\"6\"><hr></td></tr>\n";
	}
	print "<tr><th colspan=\"6\" align=\"right\"><input type=\"button\" name=\"new\" value=\"", &translate('New Rewrite'), "\" onclick=\"document.forms[0].rewrite.value=''; document.forms[0].action.value='rewritesedit'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub edit_rewrites
{
	my ($name, $else) = &normalyze(shift);

	print "<h2>", &translate('Url Rewrite Edition'), "</h2>\n";
	if ($else) {
		print "<input type=\"hidden\" name=\"else\" value=\"1\" />\n";
	}

	my $pattern = '';
	my $substitute = '';
	my $icase = '';
	my $move_temp = '';
	my $move_perm = '';
	my $null = '';
	my $val = $OLD;
	print "<table align=\"center\" width=\"100%\"><tr><td>\n";
	print "<table align=\"center\">\n";
	if (!$name) {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"text\" size=\"20\" name=\"rewrite\" value=\"\" /></td></tr>\n";
	} else {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"hidden\" name=\"rewrite\" value=\"$name\" />$name</th></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";

	if ($val =~ /^log[\s\t]+(.*)/) {
		my $value = $1;
		my $anon = '';
		if ($value =~ s/anonymous[\s\t]+//) {
			$anon = 'checked="1"';
		}
		print "<tr><th nowrap=\"1\">", &translate('Log into file'), "</th><td>";
		print "<input type=\"hidden\" name=\"srctype\" value=\"log\" />\n";
		print "<input type=\"text\" size=\"50\" name=\"srcval\" value=\"$value\" />\n";
		print &translate('anonymized'), "<input type=\"checkbox\" name=\"anonymous\" $anon />\n";
		print "</td></tr>\n";
	} elsif ($val =~ /^(within|outside)[\s\t]+(.*)/) {
		print "<tr><th nowrap=\"1\">", &translate('Schedules'), "</th><td align=\"left\">";
		print "<input type=\"hidden\" name=\"srctype\" value=\"time\" />\n";
		print "<select name=\"srcval\">\n";
		print "<option value=\"\">", &translate('All the time'), "</option>\n";
		foreach my $k (sort keys %{$CONFIG{time}}) {
			foreach my $t ('within', 'outside') {
				my $sel = '';
				$sel = 'selected="1" ' if ($val eq "$t $k");
				print "<option value=\"$t $k\" $sel>", &translate($t), " '$k'</option>\n";
			}
		}
		print "</select>\n";
		print "</td></tr>\n";
	} else {
		($null, $pattern, $substitute,$icase) = split(/\@/, $val);
		if ($icase) {
			if ($icase =~ /r/) {
				$move_temp = 'r';
			} elsif ($icase =~ /R/) {
				$move_perm = 'R';
			} elsif ($icase =~ /i/) {
				$icase = 'i';
			}
		}
		print "<tr><td nowrap=\"1\">", &translate('Replace'), " : \n";
		print "<input type=\"text\" size=\"50\" name=\"pattern\" value=\"$pattern\" /></td>\n";
		print "<td nowrap=\"1\">", &translate('with'), " : \n";
		print "<input type=\"text\" size=\"50\" name=\"substitute\" value=\"$substitute\" /></td></tr>\n";
		print "<tr><th nowrap=\"1\" colspan=\"2\">", &translate('Case insensitive'), "\n";
		my $checked = '';
		$checked = 'checked="1"' if ($icase);
		print "<input type=\"checkbox\" name=\"opts\" value=\"i\" $checked />\n";
		print "&nbsp;&nbsp;&nbsp;&nbsp;", &translate('Show move temporary'), "\n";
		$checked = '';
		$checked = 'checked="1"' if ($move_temp);
		print "<input type=\"checkbox\" name=\"opts\" value=\"r\" $checked  onchange=\"if (this.checked == true) document.forms[0].opts[2].checked=false;\"/>\n";
		print "&nbsp;&nbsp;&nbsp;&nbsp;", &translate('Show move permanently'), "\n";
		$checked = '';
		$checked = 'checked="1"' if ($move_perm);
		print "<input type=\"checkbox\" name=\"opts\" value=\"R\" $checked onchange=\"if (this.checked == true) document.forms[0].opts[1].checked=false;\"/>\n";
		print "</th></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"if (validate_rewrite() == true) { document.forms[0].apply.value='1'; document.forms[0].submit(); } return false;\"></th></tr>\n";
	print "</table>\n";
	print "</td></tr><tr><td>\n";
	print &show_help('rewrites');
	print "</td></tr></table>\n";

}

sub show_sources
{
	print "<h2>", &translate('Sources Configuration'), "</h2>\n";
	print "<input type=\"hidden\" name=\"source\" value=\"\" />\n";
	print "<table align=\"center\" width=\"80%\">\n";
	print "<tr><th align=\"left\">", &translate('Rule name'), "</th><th>&nbsp;</th><th colspan=\"2\">", &translate('Action'), "</th></tr>\n";
	print "<tr><td style=\"border: none;\" colspan=\"4\"><hr></td></tr>\n";
	foreach my $k (sort keys %{$CONFIG{src}}) {
		my $delete = 1;
		foreach my $z (keys %{$CONFIG{acl}}) {
			if ($z eq $k) {
				$delete = 0;
				last;
			}
		}
		print "<tr><th align=\"left\">$k</th><th align=\"left\">&nbsp;</th><th><a href=\"\" onclick=\"document.forms[0].source.value='$k'; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
		if ($delete) {
			print "<th><a href=\"\" onclick=\"document.forms[0].source.value='$k'; document.forms[0].action.value='sourcesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove all'), "\">$IMG_REMOVE</a></th>";
		} else {
			print "<th title=\"", &translate('Still in use'), "\">$IMG_NOREMOVE</th>";
		}
		print "\n";
		foreach my $key (sort keys %{$CONFIG{src}{$k}}) {
			next if (!grep(/^$key$/, @SRC_KEYWORD));
			foreach (@{$CONFIG{src}{$k}{$key}}) {
				print "<tr><th>&nbsp;</th><td><b>", &translate($SRC_ALIAS{$key}), "</b>: ", &show_editor($key, $_), "</td><th><a href=\"\" onclick=\"document.forms[0].source.value='$k'; document.forms[0].oldvalue.value='", &encode_url("$key $_"), "'; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
				print "<th><a href=\"\" onclick=\"document.forms[0].source.value='$k'; document.forms[0].oldvalue.value='", &encode_url("$key $_"), "'; document.forms[0].action.value='sourcesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
				print "</tr>\n";
			}
		}
		&show_log_schedule('src', 'source', $k, 0);

		if ($CONFIG{src}{$k}{outside} || $CONFIG{src}{$k}{within}) {
			print "<tr><th>", &translate('if schedule not match'), "</th><th>&nbsp;</th><th><a href=\"\" onclick=\"document.forms[0].source.value='$k-else'; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
			print "<th><a href=\"\" onclick=\"document.forms[0].source.value='$k-else'; document.forms[0].action.value='sourcesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove all'), "\">$IMG_REMOVE</a></th></tr>\n";
			foreach my $key (sort keys %{$CONFIG{src}{$k}{else}}) {
				next if (!grep(/^$key$/, @SRC_KEYWORD));
				foreach (@{$CONFIG{src}{$k}{else}{$key}}) {
					print "<tr><th>&nbsp;</th><td><b>", &translate($SRC_ALIAS{$key}), "</b>: ", &show_editor($key, $_), "</td><th><a href=\"\" onclick=\"document.forms[0].source.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url("$key $_"), "'; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
					print "<th><a href=\"\" onclick=\"document.forms[0].source.value='$k'; document.forms[0].oldvalue.value='", &encode_url("$key $_"), "'; document.forms[0].action.value='sourcesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
					print "</tr>\n";
				}
			}
			my $v = $CONFIG{src}{$k}{else}{log} || '';
			my $anon = '';
			if ($v =~ s/anonymous[\s\t]+(.*)/$1/) {
				$anon = "(" . &translate('anonymized') . ")";
			}
			if ($v) {
				print "<tr><th>&nbsp;</th><td><b>", &translate('Log file'), "</b> : ";
			} else {
				print "<tr><th>&nbsp;</th><td><b>", &translate('No log file'), "</b>";
			}
			print "$v $anon";
			print "</td><th><a href=\"\" onclick=\"document.forms[0].source.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{src}{$k}{else}{log}"), "'; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
			print "<th><a href=\"\" onclick=\"document.forms[0].source.value='$k-else'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{src}{$k}{else}{log}"), "'; document.forms[0].action.value='sourcesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
			print "</tr>\n";

		}
		print "<tr><th colspan=\"4\"><hr></th></tr>\n";
	}
	print "<tr><th colspan=\"4\" align=\"right\"><input type=\"button\" name=\"new\" value=\"", &translate('New Source'), "\" onclick=\"document.forms[0].source.value=''; document.forms[0].oldvalue.value=''; document.forms[0].action.value='sourcesedit'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub edit_sources
{
	my ($name, $else) = &normalyze(shift);

	print "<h2>", &translate('Sources Edition'), "</h2>\n";
	if ($else) {
		print "<input type=\"hidden\" name=\"else\" value=\"1\" />\n";
	}
	print "<table align=\"center\" width=\"100%\"><tr><td>\n";
	print "<table align=\"center\">\n";
	if (!$name) {
		print "<tr><th align=\"left\">", &translate('Rule name'), "</th><td><input type=\"text\" size=\"20\" name=\"src\" value=\"\" /></td></tr>\n";
	} else {
		print "<tr><th align=\"left\">", &translate('Rule name'), "</th><td><input type=\"hidden\" name=\"src\" value=\"$name\" />$name</td></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	my $val = $OLD || '';
	if ($val =~ /^log[\s\t]+(.*)/) {
		my $value = $1;
		my $anon = '';
		if ($value =~ s/anonymous[\s\t]+//) {
			$anon = 'checked="1"';
		}
		print "<tr><th nowrap=\"1\">", &translate('Log into file'), "</th><td>";
		print "<input type=\"hidden\" name=\"srctype\" value=\"log\" />\n";
		print "<input type=\"text\" size=\"50\" name=\"srcval\" value=\"$value\" />\n";
		print &translate('anonymized'), "<input type=\"checkbox\" name=\"anonymous\" $anon />\n";
		print "</td></tr>\n";
	} elsif ($val =~ /^(within|outside)[\s\t]+(.*)/) {
		print "<tr><th nowrap=\"1\">", &translate('Schedules'), "</th><td align=\"left\">";
		print "<input type=\"hidden\" name=\"srctype\" value=\"time\" />\n";
		print "<select name=\"srcval\">\n";
		print "<option value=\"\">", &translate('All the time'), "</option>\n";
		foreach my $k (sort keys %{$CONFIG{time}}) {
			foreach my $t ('within', 'outside') {
				my $sel = '';
				$sel = 'selected="1" ' if ($val eq "$t $k");
				print "<option value=\"$t $k\" $sel>", &translate($t), " '$k'</option>\n";
			}
		}
		print "</select>\n";
		print "</td></tr>\n";
	} else {
		my $type = '';
		my $value = '';
		foreach my $key (@SRC_KEYWORD) {
			if (!$else) {
				foreach (@{$CONFIG{src}{$name}{$key}}) {
					if ("$key $_" eq $val) {
						$type = $key;
						$value = $_;
						last;
					}
				}
			} else {
				foreach (@{$CONFIG{src}{$name}{else}{$key}}) {
					if ("$key $_" eq $val) {
						$type = $key;
						$value = $_;
						last;
					}
				}
			}
			last if ($value);
		}
		print "<tr><th nowrap=\"1\">", &translate('Source'), "</th><td>";
		print "<select name=\"srctype\">\n<option value=\"\"></option>\n";
		foreach my $t (@SRC_KEYWORD) {
			my $sel = '';
			$sel = 'selected="1" ' if ($t eq $type);
			print "<option value=\"$t\" $sel>", &translate($SRC_ALIAS{$t}), "</option>\n";
		}
		print "</select>\n";
		print "<input type=\"text\" size=\"50\" name=\"srcval\" value=\"$value\" /></td></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"if (validate_source() == true) { document.forms[0].apply.value='1'; document.forms[0].submit();} return false;\"></th></tr>\n";
	print "</table></td></tr><tr><td>\n";
	print &show_help('sources');
	print "</td></tr></table>\n";

}

sub show_categories
{

	my %blinfo = &get_blacklists_description();
	my @bl = &get_blacklists();

	print "<h2>", &translate('Filters Configuration'), "</h2>\n";
	print "<input type=\"hidden\" name=\"category\" value=\"\" />\n";
	if (!scalar keys %{$CONFIG{dest}}) {
		print "<p><input type=\"button\" name=\"autocreate\" value=\"", &translate('Autocreate'), "\" title=\"", &translate('Autocreate filters from blacklist database'), "\" onclick=\"document.forms[0].action.value='autocreate'; document.forms[0].submit(); return false;\"></p>\n";
	}
	print "<table align=\"center\" width=\"90%\">\n";
	print "<tr><th align=\"left\" nowrap=\"1\">", &translate('Rule name'), "</th><th align=\"left\" nowrap=\"1\">", &translate('Schedules'), "</th><th align=\"left\">", &translate('Domains'), "</th><th align=\"left\">", &translate('Urls'), "</th><th align=\"left\">", &translate('Expressions'), "</th><th align=\"left\">", &translate('Redirection'), "</th><th align=\"left\">", &translate('Log file'), "</th><th colspan=\"2\">", &translate('Action'), "</th></tr>\n";
	print "<tr><th colspan=\"9\"><hr></th></tr>\n";
	foreach my $k (sort keys %{$CONFIG{dest}}) {
		my $delete = 1;
		foreach my $z (keys %{$CONFIG{acl}}) {
			foreach my $e (@{$CONFIG{acl}{$z}{pass}}) {
				if ( ($e eq $k) || ($e eq "!$k") ) {
					$delete = 0;
					last;
				}
			}
			last if (!$delete);
		}
		my $schedule = '&nbsp;';
		if (exists $CONFIG{dest}{$k}{within}) {
			$schedule = &translate('within') . ' ' . $CONFIG{dest}{$k}{within};
		} elsif (exists $CONFIG{dest}{$k}{outside}) {
			$schedule = &translate('outside') . ' ' . $CONFIG{dest}{$k}{outside};
		}
		print "<tr><th align=\"left\" nowrap=\"1\">$k</th><td align=\"left\" nowrap=\"1\">$schedule</td>\n";
		foreach my $type ('domain', 'url', 'expression') {
			my $list = $CONFIG{dest}{$k}{$type . 'list'} || '';
			if ($list) {
				$list =~ s/\/.*//;
				$list = $blinfo{$list}{alias} || $list;
			}
			print "<td>$list</td>";
		}
		my $img = '&nbsp;';
		$img = $IMG_REDIRECT if ($CONFIG{dest}{$k}{redirect});
		print "<td nowrap=\"1\" title=\"$CONFIG{dest}{$k}{redirect}\" style=\"text-align: center;\">$img</td><td nowrap=\"1\">";
		my $v = $CONFIG{dest}{$k}{log} || '';
		my $anon = '';
		if ($v =~ s/anonymous[\s\t]+(.*)/$1/) {
			$anon = "(" . &translate('anonymized') . ")";
		}
		if ($v) {
			print "$v $anon";
		} else {
			print "&nbsp;";
		}
		print "</td><th><a href=\"\" onclick=\"document.forms[0].category.value='$k'; document.forms[0].action.value='categoriesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
		if ($delete) {
			print "<th><a href=\"\" onclick=\"document.forms[0].category.value='$k'; document.forms[0].action.value='categoriesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</th>";
		} else {
			print "<th title=\"", &translate('Still in use'), "\">$IMG_NODELETE</th>";
		}
		print "</tr>\n";

		if ($CONFIG{dest}{$k}{outside} || $CONFIG{dest}{$k}{within}) {
			print "<tr><th nowrap=\"1\" colspan=\"2\" align=\"center\">", &translate('if schedule not match'), "</th><th colspan=\"5\">&nbsp;</th>";
			if (scalar keys %{$CONFIG{dest}{$k}{else}} == 0 ) {
				print "<th><a href=\"\" onclick=\"document.forms[0].category.value='$k-else'; document.forms[0].action.value='categoriesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Add an element'), "\">$IMG_ADD</a></th>";
			}
			print "<th>&nbsp;</th></tr>\n";
			if (scalar keys %{$CONFIG{dest}{$k}{else}} > 0) {
				print "<tr><th align=\"left\" colspan=\"2\" nowrap=\"1\">&nbsp;</th>\n";
				foreach my $type ('domain', 'url', 'expression') {
					my $list = $CONFIG{dest}{$k}{else}{$type . 'list'} || '';
					if ($list) {
						$list =~ s/\/.*//;
						$list = $blinfo{$list}{alias} || $list;
					}
					print "<td>$list</td>";
				}
				print "<td nowrap=\"1\" title=\"$CONFIG{dest}{$k}{else}{redirect}\">", substr($CONFIG{dest}{$k}{else}{redirect}, 0, 60), "</td><td nowrap=\"1\">";
				my $v = $CONFIG{dest}{$k}{else}{log} || '';
				my $anon = '';
				if ($v =~ s/anonymous[\s\t]+(.*)/$1/) {
					$anon = "(" . &translate('anonymized') . ")";
				}
				if ($v) {
					print "$v $anon";
				} else {
					print "&nbsp;";
				}
				print "</td><th><a href=\"\" onclick=\"document.forms[0].category.value='$k-else'; document.forms[0].action.value='categoriesedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
				print "<th><a href=\"\" onclick=\"document.forms[0].category.value='$k-else'; document.forms[0].action.value='categoriesdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</th>";
				print "</tr>\n";
			}

		}
		print "<tr><th colspan=\"9\"><hr></th></tr>\n";
	}
	print "<tr><th colspan=\"9\" align=\"right\"><input type=\"button\" name=\"new\" value=\"", &translate('New Filter'), "\" onclick=\"document.forms[0].category.value=''; document.forms[0].action.value='categoriesedit'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub edit_categories
{
	my ($name, $else) = &normalyze(shift);
	my $default = shift;
	if ($BL && ($default) ) {
		$BL =~ s/[^a-z0-9\_\-]+//ig;
		$BL = lc($BL);
		mkdir("$CONFIG{dbhome}/$BL");
		$ACTION = 'bledit';
		$BL =~ s/\/.*//;
	}

	print "<h2>", &translate('Filters Edition'), "</h2>\n";
	if ($else) {
		print "<input type=\"hidden\" name=\"else\" value=\"1\" />\n";
	}

	my %blinfo = &get_blacklists_description();
	my @bl = &get_blacklists();

	my $domain = '';
	my $url = '';
	my $expression = '';
	my $redirect = '';
	my $log = '';
	if (!$else) {
		if (exists $CONFIG{dest}{$name}) {
			$domain = $CONFIG{dest}{$name}{'domainlist'} || '';
			$url = $CONFIG{dest}{$name}{'urllist'} || '';
			$expression = $CONFIG{dest}{$name}{'expressionlist'} || '';
			$redirect = $CONFIG{dest}{$name}{'redirect'} || '';
			$log = $CONFIG{dest}{$name}{'log'} || '';
		}
	} else {
		if (exists $CONFIG{dest}{$name}{else}) {
			$domain = $CONFIG{dest}{$name}{else}{'domainlist'} || '';
			$url = $CONFIG{dest}{$name}{else}{'urllist'} || '';
			$expression = $CONFIG{dest}{$name}{else}{'expressionlist'} || '';
			$redirect = $CONFIG{dest}{$name}{else}{'redirect'} || '';
			$log = $CONFIG{dest}{$name}{else}{'log'} || '';
		}
	}
	print "<table align=\"center\" width=\"100%\"><tr><td>\n";
	print "<table align=\"center\">\n";
	if (!$name) {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"text\" size=\"20\" name=\"category\" value=\"$default\" /></td></tr>\n";
	} else {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Rule name'), " <input type=\"hidden\" name=\"category\" value=\"$name\" />$name</th></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	if (!$else) {
		print "<tr><th align=\"right\">", &translate('Schedule'), "</th>\n";
		print "<th nowrap=\"1\" align=\"left\">";
		print "<select name=\"time\">\n";
		print "<option value=\"\">", &translate('All the time'), "</option>\n";
		foreach my $k (sort keys %{$CONFIG{time}}) {
			foreach my $t ('within', 'outside') {
				my $sel = '';
				$sel = 'selected="1" ' if ($CONFIG{dest}{$name}{$t} eq $k);
				print "<option value=\"$t $k\" $sel>", &translate($t), " $k</option>\n";
			}
		}
		print "</select>\n";
		print "</th></tr>\n";
	}
	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Search in domains list'), "</th><th align=\"left\"><select name=\"domainlist\">\n";
	print "<option value=\"\"></option>\n";
	foreach (my $j = 0; $j <= $#bl; $j++) {
		my $sel = '';
		$sel = "selected=\"1\"" if ($domain eq "$bl[$j]/domains"); 
		$sel = "selected=\"1\"" if ($default =~ /$bl[$j]/); 
		print "<option value=\"$bl[$j]/domains\" $sel>" . ($blinfo{$bl[$j]}{alias} || $bl[$j]) . "</option>\n";
	}
	print "</select>\n";
	print "</th></tr>\n";

	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Search in Urls list'), "</th><th align=\"left\"><select name=\"urllist\">\n";
	print "<option value=\"\"></option>\n";
	foreach (my $j = 0; $j <= $#bl; $j++) {
		my $sel = '';
		$sel = "selected=\"1\"" if ($url eq "$bl[$j]/urls"); 
		print "<option value=\"$bl[$j]/urls\" $sel>" . ($blinfo{$bl[$j]}{alias} || $bl[$j]) . "</option>\n";
	}
	print "</select>\n";
	print "</th></tr>\n";

	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Search in expressions list'), "</th><th align=\"left\"><select name=\"expressionlist\">\n";
	print "<option value=\"\"></option>\n";
	foreach (my $j = 0; $j <= $#bl; $j++) {
		my $sel = '';
		$sel = "selected=\"1\"" if ($expression eq "$bl[$j]/expressions"); 
		print "<option value=\"$bl[$j]/expressions\" $sel>" . ($blinfo{$bl[$j]}{alias} || $bl[$j]) . "</option>\n";
	}
	print "</select>\n";
	print "</th></tr>\n";
	print "<tr><td colspan=\"2\" align=\"left\">", &translate('When found in list above'), "</td></tr>\n";

	print "<tr><th align=\"right\">", &translate('Redirect to Url'), "</th><th align=\"left\"><input type=\"text\" size=\"50\" name=\"redirect\" value=\"", $CGI->escapeHTML($redirect), "\" /></th></tr>\n";
	my $anon = '';
	if ($log =~ s/anonymous[\s\t]+//) {
		$anon = 'checked="1"';
	}
	print "<tr><th align=\"right\">", &translate('Log to file'), "</th><th align=\"left\"><input type=\"text\" size=\"50\" name=\"log\" value=\"$log\" /> ", &translate('anonymized'), "<input type=\"checkbox\" name=\"anonymous\" $anon /></th></tr>\n";
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"if (validate_filter() == true) { document.forms[0].apply.value='1'; document.forms[0].submit(); } return false;\"></td></tr>\n";
	print "</table>\n";
	print "</td></tr><tr><td>\n";
	print &show_help('categories');
	print "</td></tr></table>\n";
	if ($default) {
		print "<input type=\"hidden\" name=\"default\" value=\"$default\">\n";
	}

}

sub show_acl
{

	my %blinfo = &get_blacklists_description();
	my @bl = &get_blacklists();

	print "<h2>", &translate('ACLs Configuration'), "</h2>\n";
	print "<input type=\"hidden\" name=\"acl\" value=\"\" />\n";
	print "<table width=\"100%\">\n";
	print "<tr><th>", &translate('Sources'), "</th><th>", &translate('Schedules'), "</th><th>", &translate('Destination'), "</th><th>", &translate('FQDN only'), "</th><th>", &translate('Url rewriting'), "</th><th>", &translate('Redirection'), "</th><th colspan=\"2\">", &translate('Actions'), "</th></tr>\n";
	print "<tr><th align=\"left\" colspan=\"8\"><hr></th></tr>\n";
	foreach my $k (sort keys %{$CONFIG{acl}}) {
		next if ($k eq 'default');
		my $allowed = '';
		my $blocked = '';
		my $filters = '';
		my $schedule = '';
		my $fqdn = '';
		my $blacklist = '';
		my $whitelist = '';
		my @dnsbl = ();
		# Show allowed first
		foreach my $s (@{$CONFIG{acl}{$k}{pass}}) {
			if ($s eq '!in-addr') {
				$fqdn = $IMG_NOIP;
				next;
			}
			my $tmp = $s;
			$tmp =~ s/\!//g;
			if (($tmp eq 'any') || ($tmp eq 'all')) {
				$tmp = &translate('All Internet');
			}
			next if ($tmp eq 'none');
			if ($tmp =~ /^dnsbl:/) {
				push(@dnsbl, $s);
			} else {
				if ($s =~ /^\!/) {
					$blocked .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
				} else {
					$allowed .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
				}
			}

		}
		$blocked = &translate('All Internet') . ", " if (!$blocked && grep(/^none$/, @{$CONFIG{acl}{$k}{pass}}));
		$allowed = &translate('All Internet') . ", " if (!$allowed && grep(/^(all|any)$/, @{$CONFIG{acl}{$k}{pass}}));
		if ($blocked =~ s/, $//) {
			$blocked = '<b>' . &translate('Blocked') . ' :</b> ' . $blocked;
		}
		if ($allowed =~ s/, $//) {
			if (grep(/^none$/, @{$CONFIG{acl}{$k}{pass}})) {
				$allowed = '<b>' . &translate('Allow only') . ' :</b> ' . $allowed;
			} else {
				$allowed = '<b>' . &translate('Allow') . ' :</b> ' . $allowed;
			}
		}
		foreach my $bl (@dnsbl) {
			if ($bl =~ s/^\!dnsbl://) {
				$blacklist .= "$bl, ";
			} elsif ($bl =~ s/^dnsbl://) {
				$whitelist .= "$bl, ";
			}
		}
		if ($blacklist =~ s/, $//) {
			$blacklist = "<br><b>" . &translate('DNS Blacklist') . ":</b> $blacklist";
		}
		if ($whitelist =~ s/, $//) {
			$whitelist = "<br><b>" . &translate('DNS Whitelist') . ":</b> $whitelist";
		}
			
		if (exists $CONFIG{acl}{$k}{extended}{within}) {
			$schedule = &translate('within') . " $CONFIG{acl}{$k}{extended}{within}";
		} elsif (exists $CONFIG{acl}{$k}{extended}{outside}) {
			$schedule = &translate('outside') . " $CONFIG{acl}{$k}{extended}{outside}";
		}
		my $rewrite = '';
		$rewrite = join(' ', @{$CONFIG{acl}{$k}{rewrite}}) if (exists $CONFIG{acl}{$k}{rewrite});
		my $img = '&nbsp;';
		$img = $IMG_REDIRECT if ($CONFIG{acl}{$k}{redirect});
		print "<tr><th align=\"left\">$k</th><td>$schedule</td><td>$allowed<br>$blocked$whitelist$blacklist</td><td style=\"text-align: center;\">$fqdn</td><td>$rewrite</td><td title=\"$CONFIG{acl}{$k}{redirect}\" style=\"text-align: center;\">$img</td><th><a href=\"\" onclick=\"document.forms[0].acl.value='$k'; document.forms[0].action.value='aclsedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th><th><a href=\"\" onclick=\"document.forms[0].acl.value='$k'; document.forms[0].action.value='aclsdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th></tr>\n";
		my $sources = '';
		if (exists $CONFIG{acl}{$k}{else}) {
			$fqdn = '';
			$allowed = '';
			$blocked = '';
			$whitelist = '';
			$blacklist = '';
			@dnsbl = ();
			foreach my $s (@{$CONFIG{acl}{$k}{else}{pass}}) {
				if ($s eq '!in-addr') {
					$fqdn = $IMG_NOIP;
					next;
				}
				my $tmp = $s;
				$tmp =~ s/\!//g;
				if (($tmp eq 'any') || ($tmp eq 'all')) {
					$tmp = &translate('All Internet');
				}
				next if ($tmp eq 'none');
				if ($tmp =~ /^dnsbl:/) {
					push(@dnsbl, $s);
				} else {
					if ($s =~ /^\!/) {
						$blocked .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
					} else {
						$allowed .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
					}
				}

			}
			$blocked = &translate('All Internet') . ", " if (!$blocked && grep(/^none$/, @{$CONFIG{acl}{$k}{else}{pass}}));
			$allowed = &translate('All Internet') . ", " if (!$allowed && grep(/^(all|any)$/, @{$CONFIG{acl}{$k}{else}{pass}}));
			if ($blocked =~ s/, $//) {
				$blocked = '<b>' . &translate('Blocked') . ' :</b> ' . $blocked;
			}
			if ($allowed =~ s/, $//) {
				if (grep(/^none$/, @{$CONFIG{acl}{$k}{else}{pass}})) {
					$allowed = '<b>' . &translate('Allow only') . ' :</b> ' . $allowed;
				} else {
					$allowed = '<b>' . &translate('Allow') . ' :</b> ' . $allowed;
				}
			}
			foreach my $bl (@dnsbl) {
				if ($bl =~ s/^\!dnsbl://) {
					$blacklist .= "$bl, ";
				} elsif ($bl =~ s/^dnsbl://) {
					$whitelist .= "$bl, ";
				}
			}
			if ($blacklist =~ s/, $//) {
				$blacklist = "<br><b>" . &translate('DNS Blacklist') . ":</b> $blacklist";
			}
			if ($whitelist =~ s/, $//) {
				$whitelist = "<br><b>" . &translate('DNS Whitelist') . ":</b> $whitelist";
			}
			$rewrite = '';
			$rewrite = join(' ', @{$CONFIG{acl}{$k}{else}{rewrite}}) if (exists $CONFIG{acl}{$k}{else}{rewrite});
			$img = '&nbsp;';
			$img = $IMG_REDIRECT if ($CONFIG{acl}{$k}{else}{redirect});
			print "<tr><th align=\"right\">", &translate('else'), "</th><td>&nbsp;</td><td>$allowed<br>$blocked$whitelist$blacklist</td><td style=\"text-align: center;\">$fqdn</td><td>", join(' ', $CONFIG{acl}{$k}{else}{rewrite}), "</td><td title=\"$CONFIG{acl}{$k}{else}{redirect}\" style=\"text-align: center;\">$img</td><td colspan=\"2\">&nbsp;</td></tr>\n";
		}
		print "<tr><th align=\"left\" colspan=\"8\"><hr></tr></tr>\n";
	}

	# Show the default ACL
	my $allowed = '';
	my $blocked = '';
	my $filters = '';
	my $schedule = '';
	my $fqdn = '';
	my $whitelist = '';
	my $blacklist = '';
	my @dnsbl = ();
	# Show allowed first
	foreach my $s (@{$CONFIG{acl}{default}{pass}}) {
		if ($s eq '!in-addr') {
			$fqdn = $IMG_NOIP;
			next;
		}
		my $tmp = $s;
		$tmp =~ s/\!//g;
		if (($tmp eq 'any') || ($tmp eq 'all')) {
			$tmp = &translate('All Internet');
		}
		next if ($tmp eq 'none');
		if ($tmp =~ /^dnsbl:/) {
			push(@dnsbl, $s);
		} else {
			if ($s =~ /^\!/) {
				$blocked .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
			} else {
				$allowed .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
			}
		}

	}
	$blocked = &translate('All Internet') . ", " if (!$blocked && grep(/^none$/, @{$CONFIG{acl}{default}{pass}}));
	$allowed = &translate('All Internet') . ", " if (!$allowed && grep(/^(all|any)$/, @{$CONFIG{acl}{default}{pass}}));
	if ($blocked =~ s/, $//) {
		$blocked = '<b>' . &translate('Blocked') . ' :</b> ' . $blocked;
	}
	if ($allowed =~ s/, $//) {
		if (grep(/^none$/, @{$CONFIG{acl}{default}{pass}})) {
			$allowed = '<b>' . &translate('Allow only') . ' :</b> ' . $allowed;
		} else {
			$allowed = '<b>' . &translate('Allow') . ' :</b> ' . $allowed;
		}
	}
	foreach my $bl (@dnsbl) {
		if ($bl =~ s/^\!dnsbl://) {
			$blacklist .= "$bl, ";
		} elsif ($bl =~ s/^dnsbl://) {
			$whitelist .= "$bl, ";
		}
	}
	if ($blacklist =~ s/, $//) {
		$blacklist = "<br><b>" . &translate('DNS Blacklist') . ":</b> $blacklist";
	}
	if ($whitelist =~ s/, $//) {
		$whitelist = "<br><b>" . &translate('DNS Whitelist') . ":</b> $whitelist";
	}
	if (exists $CONFIG{acl}{default}{extended}{within}) {
		$schedule = &translate('within') . " $CONFIG{acl}{default}{extended}{within}";
	} elsif (exists $CONFIG{acl}{default}{extended}{outside}) {
		$schedule = &translate('outside') . " $CONFIG{acl}{default}{extended}{outside}";
	}
	my $rewrite = '';
	$rewrite = join(' ', @{$CONFIG{acl}{default}{rewrite}}) if (exists $CONFIG{acl}{default}{rewrite});
	my $img = '&nbsp;';
	$img = $IMG_REDIRECT if ($CONFIG{acl}{default}{redirect});
	print "<tr><th align=\"left\">", &translate('Default ACL'), "</th><td>$schedule</td><td>$allowed<br>$blocked$whitelist$blacklist</td><td style=\"text-align: center;\">$fqdn</td><td>$rewrite</td><td title=\"$CONFIG{acl}{default}{redirect}\" style=\"text-align: center;\">$img</td><th><a href=\"\" onclick=\"document.forms[0].acl.value='default'; document.forms[0].action.value='aclsedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th><th>&nbsp;</th></tr>\n";
	my $sources = '';
	if (exists $CONFIG{acl}{default}{else}) {
		$fqdn = '';
		$allowed = '';
		$blocked = '';
		$whitelist = '';
		$blacklist = '';
		@dnsbl = ();
		foreach my $s (@{$CONFIG{acl}{default}{else}{pass}}) {
			if ($s eq '!in-addr') {
				$fqdn = $IMG_NOIP;
				next;
			}
			my $tmp = $s;
			$tmp =~ s/\!//g;
			if (($tmp eq 'any') || ($tmp eq 'all')) {
				$tmp = &translate('All Internet');
			}
			next if ($tmp eq 'none');
			if ($tmp =~ /^dnsbl:/) {
				push(@dnsbl, $s);
			} else {
				if ($s =~ /^\!/) {
					$blocked .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
				} else {
					$allowed .= ($blinfo{$tmp}{alias} || $tmp) . ", ";
				}
			}

		}
		$blocked = &translate('All Internet') . ", " if (!$blocked && grep(/^none$/, @{$CONFIG{acl}{default}{else}{pass}}));
		$allowed = &translate('All Internet') . ", " if (!$allowed && grep(/^(all|any)$/, @{$CONFIG{acl}{default}{else}{pass}}));
		if ($blocked =~ s/, $//) {
			$blocked = '<b>' . &translate('Blocked') . ' :</b> ' . $blocked;
		}
		if ($allowed =~ s/, $//) {
			if (grep(/^none$/, @{$CONFIG{acl}{default}{else}{pass}})) {
				$allowed = '<b>' . &translate('Allow only') . ' :</b> ' . $allowed;
			} else {
				$allowed = '<b>' . &translate('Allow') . ' :</b> ' . $allowed;
			}
		}
		foreach my $bl (@dnsbl) {
			if ($bl =~ s/^\!dnsbl://) {
				$blacklist .= "$bl, ";
			} elsif ($bl =~ s/^dnsbl://) {
				$whitelist .= "$bl, ";
			}
		}
		if ($blacklist =~ s/, $//) {
			$blacklist = "<br><b>" . &translate('DNS Blacklist') . ":</b> $blacklist";
		}
		if ($whitelist =~ s/, $//) {
			$whitelist = "<br><b>" . &translate('DNS Whitelist') . ":</b> $whitelist";
		}
		$rewrite = '';
		$rewrite = join(' ', @{$CONFIG{acl}{default}{else}{rewrite}}) if (exists $CONFIG{acl}{default}{else}{rewrite});
		$img = '&nbsp;';
		$img = $IMG_REDIRECT if ($CONFIG{acl}{default}{else}{redirect});
		print "<tr><th align=\"right\">", &translate('else'), "</th><td>&nbsp;</td><td>$allowed<br>$blocked$whitelist$blacklist</td><td style=\"text-align: center;\">$fqdn</td><td>", join(' ', $CONFIG{acl}{default}{else}{rewrite}), "</td><td title=\"$CONFIG{acl}{default}{else}{redirect}\" style=\"text-align: center;\">$img</td><td colspan=\"2\">&nbsp;</td></tr>\n";
	}
	print "<tr><th align=\"left\" colspan=\"8\"><hr></tr></tr>\n";


	print "<tr><th colspan=\"8\" align=\"right\"><input type=\"button\" name=\"new\" value=\"", &translate('New Policy'), "\" onclick=\"document.forms[0].acl.value=''; document.forms[0].action.value='aclsedit'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub edit_acls
{
	my ($name) = &normalyze(shift);

	# Get all DNS List
	my @BLDNS = split(/[,;\s\t]+/, $DNSBL);
	foreach my $a (%{$CONFIG{acl}}) {
		foreach my $d (@{$CONFIG{acl}{$a}{pass}}) {
			if ($d =~ /^[^:]+:(.*)/) {
				push(@BLDNS, $1) if (!grep(/^$1$/, @BLDNS));
			}
		}
		foreach my $d (@{$CONFIG{acl}{$a}{else}{pass}}) {
			if ($d =~ /^[^:]+:(.*)/) {
				push(@BLDNS, $1) if (!grep(/^$1$/, @BLDNS));
			}
		}
	}

	print "<h2>", &translate('Policy Edition'), "</h2>\n";

	if ( !scalar keys %{$CONFIG{src}} && ($name ne 'default') ) {
		&error(&translate('You must define some sources before'));
		return;
	}
	my %blinfo = &get_blacklists_description();
	my @bl = &get_blacklists();

	print "<table align=\"center\" width=\"100%\">\n";
	print "<tr><td valign=\"top\">\n";
	print "<table align=\"center\">\n";
	if (!$name) {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Source name'), " ";
		print "<select name=\"acl\">\n";
		print "<option value=\"\">", &translate('Select a source'), "</option>\n";
		foreach my $k (sort keys %{$CONFIG{src}}) {
			if (!exists $CONFIG{acl}{$k}) {
				print "<option value=\"$k\">$k</option>\n";
			}
		}
		print "</select></td></tr>\n";
	} else {
		print "<tr><th colspan=\"2\" align=\"left\">", &translate('Source name'), " <input type=\"hidden\" name=\"acl\" value=\"$name\" />$name</th></tr>\n";
	}
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";

	print "<tr><th align=\"left\">", &translate('Schedules'), "</th>\n";
	print "<th nowrap=\"1\" align=\"left\">";
	print "<select name=\"time\" onchange=\"conditional_status(this.selectedIndex);\">\n";
	print "<option value=\"\">", &translate('All the time'), "</option>\n";
	foreach my $k (sort keys %{$CONFIG{time}}) {
		foreach my $t ('within', 'outside') {
			my $sel = '';
			$sel = 'selected="1" ' if (exists $CONFIG{acl}{$name}{extended}{$t} && ($CONFIG{acl}{$name}{extended}{$t} eq $k) );
			print "<option value=\"$t $k\" $sel>", &translate($t), " $k</option>\n";
		}
	}
	print "</select>\n";
	print "</th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th nowrap=\"1\" align=\"left\">&nbsp;</th>";
	my $sel = '';
	$sel = 'checked="1" ' if (grep(/^\!in-addr$/, @{$CONFIG{acl}{$name}{pass}}));
	print "<td><input type=\"checkbox\" name=\"dest\" value=\"!in-addr\" $sel>\n";
	print " ", &translate('Deny ip addresses in Urls'), "</td></tr>\n";

	$sel = '';
	$sel = 'checked="1" ' if (grep(/^none$/, @{$CONFIG{acl}{$name}{pass}}));
	print "<tr><th nowrap=\"1\" style=\"text-align: right;\">", &translate('Default access'), "</ht><td>",
	"<input type=\"radio\" name=\"dest\" value=\"none\" $sel>", &translate('Only the selected list'), " (none)";
	$sel = '';
	$sel = 'checked="1" ' if (!grep(/^none$/, @{$CONFIG{acl}{$name}{pass}}));
	print "<input type=\"radio\" name=\"dest\" value=\"all\" $sel>", &translate('All Internet'), "  (all | any)</td><th></tr>\n";

	print "<tr><th nowrap=\"1\" style=\"text-align: right;\">", &translate('Allow access to'), "</th><th>\n";
	my $i = 0;
	print "<table align=\"left\"><tr>\n";
	foreach my $k (sort keys %{$CONFIG{dest}}) {
		next if ( ($k eq 'any') || ($k eq 'all') || ($k eq 'none') );
		$sel = '';
		$sel = 'checked="1" ' if (grep(/^$k$/, @{$CONFIG{acl}{$name}{pass}}));
		print "</tr><tr>" if ($i && (($i % 6) == 0) && ($i < scalar keys %{$CONFIG{dest}}));
		print "<td nowrap=\"1\"><input type=\"checkbox\" name=\"dest\" value=\"$k\" $sel>$k</td>\n";
		$i++;
	}
	print "</tr></table>\n";
	print "</th></tr>\n";
	if ($SG_VER >= 1.5) {
		print "<tr><th nowrap=\"1\" align=\"right\">", &translate('DNS Whitelist'), "</th><td>\n";
		foreach my $d (@BLDNS) {
			$sel = '';
			$sel = 'checked="1" ' if (grep(/^dnsbl:$d$/, @{$CONFIG{acl}{$name}{pass}}));
			print "<input type=\"checkbox\" name=\"dest\" value=\"dnsbl:$d\" $sel>$d\n";
		}
		print "</td></tr>\n";
	}
	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Deny access to'), "</th><th>\n";
	print "<table><tr>\n";
	$i = 0;
	foreach my $k (sort keys %{$CONFIG{dest}}) {
		next if ( ($k eq 'any') || ($k eq 'none') || ($k eq 'all'));
		$sel = '';
		$sel = 'checked="1" ' if (grep(/^\!$k$/, @{$CONFIG{acl}{$name}{pass}}));
		print "</tr><tr>" if ($i && (($i % 6) == 0) && ($i < scalar keys %{$CONFIG{dest}}));
		print "<td nowrap=\"1\"><input type=\"checkbox\" name=\"dest\" value=\"\!$k\" $sel>$k</td>\n";
		$i++;
	}
	print "</tr></table>\n";
	print "</th></tr>\n";
	if ($SG_VER >= 1.5) {
		print "<tr><th nowrap=\"1\" align=\"right\">", &translate('DNS Blacklist'), "</th><td>\n";
		foreach my $d (@BLDNS) {
			$sel = '';
			$sel = 'checked="1" ' if (grep(/^\!dnsbl:$d$/, @{$CONFIG{acl}{$name}{pass}}));
			print "<input type=\"checkbox\" name=\"dest\" value=\"!dnsbl:$d\" $sel>$d\n";
		}
		print "</td></tr>\n";
	}

	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Rewrite rules'), "</th><td>\n";
	foreach my $r (sort keys %{$CONFIG{rew}}) {
		my $sel = '';
		$sel = 'checked="1" ' if grep(/^[\!]*$r$/, @{$CONFIG{acl}{$name}{rewrite}});
		print "<input type=\"checkbox\" name=\"rew\" value=\"$r\" $sel>$r\n";
	}
	print "</td></tr>\n";

	print "<tr><th align=\"right\">", &translate('Redirect url'), "</th><td><input type=\"text\" size=\"50\" name=\"redirect\" value=\"", $CGI->escapeHTML($CONFIG{acl}{$name}{redirect}), "\" /></td></tr>\n";
	print "<tr><th align=\"right\">", &translate('Log file'), "</th><td><input type=\"text\" size=\"50\" name=\"log\" value=\"$CONFIG{acl}{$name}{log}\" /></td></tr>\n";

	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";

	print "<tr><th colspan=\"2\" align=\"left\">", &translate('else'), " ", &translate('if schedule not match'), "</th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th nowrap=\"1\" align=\"left\">&nbsp;</th>";;
	$sel = '';
	$sel = 'checked="1" ' if (grep(/^\!in-addr$/, @{$CONFIG{acl}{$name}{else}{pass}}));
	print "<td><input type=\"checkbox\" name=\"edest\" value=\"!in-addr\" $sel>";
	print " ", &translate('Deny ip addresses in Urls'), "</td></tr>\n";

	$sel = '';
	$sel = 'checked="1" ' if (grep(/^none$/, @{$CONFIG{acl}{$name}{else}{pass}}));
	print "<tr><th nowrap=\"1\" style=\"text-align: right;\">", &translate('Default access'), "</ht><td><input type=\"radio\" name=\"edest\" value=\"none\" $sel>", &translate('Only the selected list'), " (none)";
	$sel = '';
	$sel = 'checked="1" ' if (grep(/^all$/, @{$CONFIG{acl}{$name}{else}{pass}}));
	print "<input type=\"radio\" name=\"radio\" value=\"all\" $sel>", &translate('All Internet'), " (all | any)</td><th></tr>\n";

	print "<tr><th nowrap=\"1\" style=\"text-align: right;\">", &translate('Allow access to'), "</th><th>\n";
	$i = 0;
	print "<table align=\"left\"><tr>\n";
	foreach my $k (sort keys %{$CONFIG{dest}}) {
		next if ( ($k eq 'any') || ($k eq 'all') || ($k eq 'none') );
		$sel = '';
		$sel = 'checked="1" ' if (grep(/^$k$/, @{$CONFIG{acl}{$name}{else}{pass}}));
		print "</tr><tr>" if ($i && (($i % 6) == 0) && ($i < scalar keys %{$CONFIG{dest}}));
		print "<td nowrap=\"1\"><input type=\"checkbox\" name=\"edest\" value=\"$k\" $sel>$k</td>\n";
		$i++;
	}
	print "</tr></table>\n";
	print "</th></tr>\n";
	if ($SG_VER >= 1.5) {
		print "<tr><th nowrap=\"1\" align=\"right\">", &translate('DNS Whitelist'), "</th><td>\n";
		foreach my $d (@BLDNS) {
			$sel = '';
			$sel = 'checked="1" ' if (grep(/^dnsbl:$d$/, @{$CONFIG{acl}{$name}{else}{pass}}));
			print "<input type=\"checkbox\" name=\"edest\" value=\"dnsbl:$d\" $sel>$d\n";
		}
		print "</td></tr>\n";
	}
	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Deny access to'), "</th><th>\n";
	print "<table><tr>\n";
	$i = 0;
	foreach my $k (sort keys %{$CONFIG{dest}}) {
		next if ( ($k eq 'any') || ($k eq 'none') || ($k eq 'all'));
		$sel = '';
		$sel = 'checked="1" ' if (grep(/^\!$k$/, @{$CONFIG{acl}{$name}{else}{pass}}));
		print "</tr><tr>" if ($i && (($i % 6) == 0) && ($i < scalar keys %{$CONFIG{dest}}));
		print "<td nowrap=\"1\"><input type=\"checkbox\" name=\"edest\" value=\"\!$k\" $sel>$k</td>\n";
		$i++;
	}
	print "</tr></table>\n";
	print "</th></tr>\n";
	if ($SG_VER >= 1.5) {
		print "<tr><th nowrap=\"1\" align=\"right\">", &translate('DNS Blacklist'), "</th><td>\n";
		foreach my $d (@BLDNS) {
			$sel = '';
			$sel = 'checked="1" ' if (grep(/^\!dnsbl:$d$/, @{$CONFIG{acl}{else}{$name}{pass}}));
			print "<input type=\"checkbox\" name=\"edest\" value=\"!dnsbl:$d\" $sel>$d\n";
		}
		print "</td></tr>\n";
	}

	print "<tr><th nowrap=\"1\" align=\"right\">", &translate('Rewrite rules'), "</th><td>\n";
	foreach my $k (sort keys %{$CONFIG{rew}}) {
		my $sel = '';
		$sel = 'checked="1" ' if (grep(/^[\!]*$k$/, @{$CONFIG{acl}{$name}{else}{rewrite}}));
		print "<input type=\"checkbox\" name=\"erew\" value=\"$k\" $sel>$k\n";
	}
	print "</td></tr>\n";

	print "<tr><th align=\"right\">", &translate('Redirect url'), "</th><td><input type=\"text\" size=\"50\" name=\"eredirect\" value=\"", $CGI->escapeHTML($CONFIG{acl}{$name}{else}{redirect}), "\" /></td></tr>\n";
	print "<tr><th align=\"right\">", &translate('Log file'), "</th><td><input type=\"text\" size=\"50\" name=\"elog\" value=\"$CONFIG{acl}{$name}{else}{log}\" /></td></tr>\n";
	print "<tr><th colspan=\"2\"><hr /></th></tr>\n";

	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"if (validate_policy() == true) { document.forms[0].apply.value='1'; document.forms[0].submit(); } return false;\"></td></tr>\n";
	print "</table>\n";
	print "</td><td valign=\"top\">\n";
	print &show_help('acl');
	print "</td></tr></table>\n";

}

sub show_config
{

	print "<h2>SquidGuard configuration</h2>\n";
	print "<table align=\"center\" width=\"80%\">\n";
	print "<tr><th align=\"left\">File: $CONF_FILE</th></tr>\n";
	print "<tr><th><hr /></th></tr>\n";
	print "<tr><th  align=\"left\"><pre>\n";

	print &dump_config() if (-e $CONF_FILE);

	print "</pre></td></tr>\n";
	print "</table>\n";

}

sub dump_config
{

	my $config = '';
	$config .= "# Global variables\n";
	foreach my $g (@GLOBALVAR) {
		$config .= "$g\t$CONFIG{$g}\n" if ($CONFIG{$g});
	}

	$config .= "\n# Time rules\n";
	$config .= "# abbrev for weekdays:\n";
	$config .= "# s = sun, m = mon, t =tue, w = wed, h = thu, f = fri, a = sat\n";
	foreach my $t (sort keys %{$CONFIG{time}}) {
		$config .= "time $t {\n";
		foreach my $v (@{$CONFIG{time}{$t}{days}}) {
			$v =~ s/\|/ /;
			if ($v =~ /^[0-9\*]+\.[0-9\*]+\.[0-9\*]+/) {
				$config .= "\tdate $v\n";
			} else {
				$config .= "\tweekly $v\n";
			}
		}
		$config .= "}\n";
	}

	$config .= "\n# Source addresses\n";
	foreach my $t (sort keys %{$CONFIG{src}}) {
#		if ($CONFIG{src}{$t}{'outside'}) {
#			$config .= "src $t outside $CONFIG{src}{$t}{'outside'} {\n";
#		} elsif ($CONFIG{src}{$t}{'within'}) {
#			$config .= "src $t within $CONFIG{src}{$t}{'within'} {\n";
#		} else {
			$config .= "src $t {\n";
#		}
		foreach my $k (@SRC_KEYWORD) {
			foreach my $v (@{$CONFIG{src}{$t}{$k}}) {
				$config .= "\t$k\t$v\n";
			}
		}
		if ($CONFIG{src}{$t}{within}) {
			$config .= "\twithin\t$CONFIG{src}{$t}{within}\n";
		}
		if ($CONFIG{src}{$t}{outside}) {
			$config .= "\toutside\t$CONFIG{src}{$t}{outside}\n";
		}
		if ($CONFIG{src}{$t}{log}) {
			$config .= "\tlog\t$CONFIG{src}{$t}{log}\n";
		}
		if (exists $CONFIG{src}{$t}{else} && (scalar keys %{$CONFIG{src}{$t}{else}} > 0) ) {
			$config .= "} else {\n";
			foreach my $k (@SRC_KEYWORD) {
				foreach my $v (@{$CONFIG{src}{$t}{else}{$k}}) {
					$config .= "\t$k\t$v\n";
				}
			}
			if ($CONFIG{src}{$t}{else}{log}) {
				$config .= "\tlog\t$CONFIG{src}{$t}{else}{log}\n";
			}
		}
		$config .= "}\n";
	}

	$config .= "\n# Destination classes\n";
	foreach my $t (sort keys %{$CONFIG{dest}}) {
#		if ($CONFIG{dest}{$t}{'outside'}) {
#			$config .= "dest $t outside $CONFIG{dest}{$t}{'outside'} {\n";
#		} elsif ($CONFIG{dest}{$t}{'within'}) {
#			$config .= "dest $t within $CONFIG{dest}{$t}{'within'} {\n";
#		} else {
			$config .= "dest $t {\n";
#			delete $CONFIG{dest}{$t}{'else'};
#		}
		foreach my $k (sort keys %{$CONFIG{dest}{$t}}) {
			next if (grep(/^$k$/, 'else'));
			$config .= "\t$k\t$CONFIG{dest}{$t}{$k}\n";
		}
		if (exists $CONFIG{dest}{$t}{else} && (scalar keys %{$CONFIG{dest}{$t}{else}} > 0) ) {
			$config .= "} else {\n";
			foreach my $k (sort keys %{$CONFIG{dest}{$t}{else}}) {
				$config .= "\t$k\t$CONFIG{dest}{$t}{else}{$k}\n";
			}
		}
		$config .= "}\n";
	}

	$config .= "\n# Rewrite rules\n";
	foreach my $t (sort keys %{$CONFIG{rew}}) {
#		if ($CONFIG{rew}{$t}{'outside'}) {
#			$config .= "rew $t outside $CONFIG{rew}{$t}{'outside'} {\n";
#		} elsif ($CONFIG{rew}{$t}{'within'}) {
#			$config .= "rew $t within $CONFIG{rew}{$t}{'within'} {\n";
#		} else {
			$config .= "rew $t {\n";
#		}
		foreach my $v (@{$CONFIG{rew}{$t}{rewrite}}) {
			$config .= "\t$v\n";
		}
		if ($CONFIG{rew}{$t}{within}) {
			$config .= "\twithin $CONFIG{rew}{$t}{within}\n";
		}
		if ($CONFIG{rew}{$t}{outside}) {
			$config .= "\toutside $CONFIG{rew}{$t}{outside}\n";
		}
		if ($CONFIG{rew}{$t}{log}) {
			$config .= "\tlog $CONFIG{rew}{$t}{log}\n";
		}
		if (exists $CONFIG{rew}{$t}{else} && (scalar keys %{$CONFIG{rew}{$t}{else}} > 0) ) {
			$config .= "} else {\n";
			foreach my $v (@{$CONFIG{rew}{$t}{else}{rewrite}}) {
				$config .= "\t$v\n";
			}
			if ($CONFIG{rew}{$t}{else}{log}) {
				$config .= "\tlog\t$CONFIG{rew}{$t}{else}{log}\n";
			}
		}
		$config .= "}\n";
	}

	$config .= "\n# Policies\n";
	$config .= "acl {\n";
	foreach my $t (sort keys %{$CONFIG{acl}}) {
		next if ($t eq 'default');
		my $extended = '';
		if (exists $CONFIG{acl}{$t}{extended}{within}) {
			$config .= "\t$t within $CONFIG{acl}{$t}{extended}{within} {\n";
		} elsif (exists $CONFIG{acl}{$t}{extended}{outside}) {
			$config .= "\t$t outside $CONFIG{acl}{$t}{extended}{outside} {\n";
		} else {
			$config .= "\t$t {\n";
		}
		foreach my $v (sort keys %{$CONFIG{acl}{$t}}) {
			next if ( ($v eq 'extended') || ($v eq 'else') );
			if ($v eq 'rewrite') {
				$config .= "\t\t$v\t" . join(' ', @{$CONFIG{acl}{$t}{$v}}) . "\n";
			} elsif ($v ne 'pass') {
				$config .= "\t\t$v\t$CONFIG{acl}{$t}{$v}\n";
			} else {
				$config .= "\t\t$v\t";
				my $last = '';
				foreach (@{$CONFIG{acl}{$t}{$v}}) {
					if (($_ eq 'none') || ($_ eq 'all')) {
						$last = $_;
						next;
					}
					$config .= "$_ ";
				}
				$config .= "$last\n";
			}
		}
		if (exists $CONFIG{acl}{$t}{else}) {
			$config .= "\t} else {\n";
			foreach my $v (sort keys %{$CONFIG{acl}{$t}{else}}) {
				if ($v ne 'pass') {
					$config .= "\t\t$v\t$CONFIG{acl}{$t}{else}{$v}\n";
				} else {
					$config .= "\t\t$v\t";
					my $last = '';
					foreach (@{$CONFIG{acl}{$t}{else}{$v}}) {
						if (($_ eq 'none') || ($_ eq 'all')) {
							$last = $_;
							next;
						}
						$config .= "$_ ";
					}
					$config .= "$last\n";
				}
			}
		}
		$config .= "\t}\n";
	}
	my $extended = '';
	if (exists $CONFIG{acl}{default}{extended}{within}) {
		$config .= "\tdefault within $CONFIG{acl}{default}{extended}{within} {\n";
	} elsif (exists $CONFIG{acl}{default}{extended}{outside}) {
		$config .= "\tdefault outside $CONFIG{acl}{default}{extended}{outside} {\n";
	} else {
		$config .= "\tdefault {\n";
	}
	foreach my $v (sort keys %{$CONFIG{acl}{default}}) {
		next if ( ($v eq 'extended') || ($v eq 'else') );
		if ($v eq 'rewrite') {
			$config .= "\t\t$v\t" . join(' ', @{$CONFIG{acl}{default}{$v}}) . "\n";
		} elsif ($v ne 'pass') {
			$config .= "\t\t$v\t$CONFIG{acl}{default}{$v}\n";
		} else {
			$config .= "\t\t$v\t" . join(' ', @{$CONFIG{acl}{default}{$v}}) . "\n";
		}
	}
	if (exists $CONFIG{acl}{default}{else} && (scalar keys %{$CONFIG{acl}{default}{else}} > 0)) {
		$config .= "\t} else {\n";
		foreach my $v (sort keys %{$CONFIG{acl}{default}{else}}) {
			if ($v ne 'pass') {
				$config .= "\t\t$v\t$CONFIG{acl}{default}{else}{$v}\n";
			} else {
				$config .= "\t\t$v\t" . join(' ', @{$CONFIG{acl}{default}{else}{$v}}) . "\n";
			}
		}
	}
	$config .= "\t}\n";
	$config .= "}\n";

	return $config;
}

sub save_config
{

	my $content = &dump_config();

	if (not open(OUT, ">$CONF_FILE")) {
		$ERROR = "Can't save configuration to file $CONF_FILE: $!\n";
		return 0;
	}
	print OUT "$content\n";
	close(OUT);

	return 1;
}

sub show_listcontent
{
	my $bl = shift;

	print $CGI->header();
	print $CGI->start_html(
		-title  => "$PROGRAM v$VERSION",
		-author => "$AUTHOR",
		-meta   => { 'copyright' => $COPYRIGHT },
		-style  => { -src => $CSS_FILE },
		-script  => { -src => $JS_FILE },
	);
	print $CGI->start_form();
	print "<input type=\"hidden\" name=\"apply\" value=\"\" />\n";
	print "<input type=\"hidden\" name=\"filelist\" value=\"$bl\" />\n";

	if (!$bl || !-e "$CONFIG{dbhome}/$bl") {
		&error("No file set");
		print "<input type=\"button\" name=\"save\" value=\"", &translate('Close'), "\" onclick=\"window.close(); return false;\">\n";
	} else {
		print "<h2>", &translate('List'), " : $bl</h2>\n";

		if (not open(IN, "$CONFIG{dbhome}/$bl")) {
			&error("Can't read file $CONFIG{dbhome}/$bl: $!");
		} else {
			print "<table><tr><th align=\"left\">\n";
			print "<textarea name=\"content\" cols=\"45\" rows=\"42\" wrap=\"off\">\n";
			while (<IN>) {
				print "$_";
			}
			close(IN);
			print "</textarea>\n";
			print "</th></tr>\n";
			print "<tr><th align=\"center\"></th></tr>\n";
			print "<tr><th><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
			print "</table>\n";
		}
	}
	print $CGI->end_form();
	print $CGI->end_html();
}

sub save_listcontent
{
	my $bl = shift;

	print $CGI->header();
	print $CGI->start_html(
		-title  => "$PROGRAM v$VERSION",
		-author => "$AUTHOR",
		-meta   => { 'copyright' => $COPYRIGHT },
		-style  => { -src => $CSS_FILE },
		-script  => { -src => $JS_FILE },
	);
	print $CGI->start_form();
	print "<input type=\"hidden\" name=\"apply\" value=\"\" />\n";
	print "<input type=\"hidden\" name=\"filelist\" value=\"$bl\" />\n";

	my $content = $CGI->param('content') || '';
	$content =~ s/
//gs;
	my @datas = split(/\n+/, $content);
	$content = '';
	map { s/^[\s]+//; s/[\s]+$//; } @datas;
	if (not open(OUT, ">$CONFIG{dbhome}/$bl.tmp")) {
		&error("Can't read file $bl.tmp: $!");
	} else {
		foreach my $l (@datas) {
			print OUT "$l\n" if ($l);
		}
		close(OUT);
	}
	if (-e "$CONFIG{dbhome}/$bl") {
		# Create a diff file
		if ($DIFF) {
			`$DIFF -U 0 $CONFIG{dbhome}/$bl $CONFIG{dbhome}/$bl.tmp  | $GREP -v "^\@\@" | $GREP -v "^--- " | $GREP -v "^+++ " > $CONFIG{dbhome}/$bl.tmpdiff`;
			print `$SQUIDGUARD -u $CONFIG{dbhome}/$bl.tmpdiff`;
			# Save diff into the historical file.
			if ($KEEP_DIFF) {
				if (open(IN, "$CONFIG{dbhome}/$bl.tmpdiff")) {
					my @text = <IN>;
					close(IN);
					if (open(OUT, ">>$CONFIG{dbhome}/$bl.diff.hist")) {
						print OUT @text;
						close(OUT);
					} else {
						&error("Can't write to file $CONFIG{dbhome}/$bl.diff.hist: $!");
					}
				} else {
					&error("Can't read file $CONFIG{dbhome}/$bl.tmpdiff: $!");
				}
			}
			unlink("$CONFIG{dbhome}/$bl.tmpdiff");
		}
		unlink("$CONFIG{dbhome}/$bl");
	} else {
		$DIFF = '';
	}
	rename("$CONFIG{dbhome}/$bl.tmp", "$CONFIG{dbhome}/$bl");
	if (!$DIFF) {
		&rebuild_database($bl);
	}
	print "<h2>", &translate('List'), " : $bl</h2>\n";

	print "<table><tr><th><input type=\"button\" name=\"save\" value=\"", &translate('Close'), "\" onclick=\"window.close(); return false;\"></th></tr></table>\n";


	print $CGI->end_form();
	print $CGI->end_html();

}

sub apply_change
{

	# Update Global variables
	if (defined $CGI->param('dbhome')) {
		foreach my $g (@GLOBALVAR) {
			$CONFIG{$g} = $CGI->param($g) || '';
			if ($g eq 'dbhome' && !-d $CGI->param($g)) {
				$ERROR = "Databases home directory " . $CGI->param($g) . " doesn't exists";
			} elsif ($g eq 'logdir' && !-d $CGI->param($g)) {
				$ERROR = "Log directory " . $CGI->param($g) . " doesn't exists";
			}
		}
	}

	# Update Time rules
	if ($CGI->param('time') && ($CGI->param('week') || $CGI->param('date'))) {
		my ($name) = &normalyze($CGI->param('time') || '');
		my $week = '';
		my @turned_on = $CGI->param('week');
		foreach my $d (@turned_on) {
			$week .= $d;
		}
		my $date = '';
		if (!$week) {
			$date = $CGI->param('date') || '';
		}
		my $starth = $CGI->param('starthour') || '';
		my $startm = $CGI->param('startmin') || '';
		my $endh = $CGI->param('endhour') || '';
		my $endm = $CGI->param('endmin') || '';

		my $oldval = $OLD;
		if ($oldval) {
			for (my $i = 0; $i <= $#{$CONFIG{time}{$name}{days}}; $i++) {
				if ($CONFIG{time}{$name}{days}[$i] eq "$oldval") {
					$CONFIG{time}{$name}{days}[$i] = ($week || $date);
					$CONFIG{time}{$name}{days}[$i] .= "|$starth:$startm-$endh:$endm" if ($starth ne '');
					last;
				}
			}
		} else {
			push(@{$CONFIG{time}{$name}{days}}, ($week || $date));
			${$CONFIG{time}{$name}{days}}[-1] .= "|$starth:$startm-$endh:$endm" if ($starth ne '');
		}
		$ACTION = 'times';

	} elsif ($CGI->param('schedule')) {
		# Delete Time rules
		my $name = $CGI->param('schedule') || '';
		my $oldval = $OLD;
		if ($oldval) {
			my @days = ();
			for (my $i = 0; $i <= $#{$CONFIG{time}{$name}{days}}; $i++) {
				if ($CONFIG{time}{$name}{days}[$i] ne "$oldval") {
					push(@days, $CONFIG{time}{$name}{days}[$i]);
				}
			}
			@{$CONFIG{time}{$name}{days}} = @days;
		} else {
			delete $CONFIG{time}{$name}{days};
		}
		$ACTION = 'times';
	}

	# Update rewrite rules
	if ($CGI->param('rewrite')) {
		my $name = $CGI->param('rewrite') || '';
		my $else = $CGI->param('else') || '';
		my $tmp = '';
		($name, $tmp) = &normalyze($name);
		$else = $tmp if ($tmp);
		my $patt = $CGI->param('pattern') || '';
		my $subst = $CGI->param('substitute') || '';
		my @opt = $CGI->param('opts');
		my $type = $CGI->param('srctype') || '';
		my $srcval = $CGI->param('srcval') || '';
		my $oldval = $OLD;
		my $anonymous = $CGI->param('anonymous') || '';
		$oldval = '' if ($oldval =~ /^(log|within|outside) $/);
		if ($ACTION ne 'rewritesdelete') {
			if ($type eq 'log') {
				$srcval = 'anonymous ' . $srcval if ($anonymous eq 'on');
				if ($else) {
					$CONFIG{rew}{$name}{else}{$type} = $srcval;
				} else {
					$CONFIG{rew}{$name}{$type} = $srcval;
				}
			} elsif ($type eq 'time') {
				delete $CONFIG{rew}{$name}{within};
				delete $CONFIG{rew}{$name}{outside};
				($type, $srcval) = split(/[\s\t]+/, $srcval, 2);
				$CONFIG{rew}{$name}{$type} = $srcval;
			} else {
				if ($oldval) {
					if ($else) {
						for (my $i = 0; $i <= $#{$CONFIG{rew}{$name}{else}{rewrite}}; $i++) {
							if ($CONFIG{rew}{$name}{else}{rewrite}[$i] eq $oldval) {
								$CONFIG{rew}{$name}{else}{rewrite}[$i] = 's@' . $patt . '@' . $subst . '@' . join('', sort @opt);
								last;
							}
						}
					} else {
						for (my $i = 0; $i <= $#{$CONFIG{rew}{$name}{rewrite}}; $i++) {
							if ($CONFIG{rew}{$name}{rewrite}[$i] eq $oldval) {
								$CONFIG{rew}{$name}{rewrite}[$i] = 's@' . $patt . '@' . $subst . '@' . join('', sort @opt);
								last;
							}
						}
					}
				} else {
					if ($else) {
						push(@{$CONFIG{rew}{$name}{else}{rewrite}}, 's@' . $patt . '@' . $subst . '@' . join('', sort @opt)) if ($patt && $subst);
					} else {
						push(@{$CONFIG{rew}{$name}{rewrite}}, 's@' . $patt . '@' . $subst . '@'. join('', sort @opt)) if ($patt && $subst);
					}
				}
			}
		} elsif ($oldval) {
			my @rewrites = ();
			if ($else) {
				for (my $i = 0; $i <= $#{$CONFIG{rew}{$name}{else}{rewrite}}; $i++) {
					if ($CONFIG{rew}{$name}{else}{rewrite}[$i] ne $oldval) {
						
						push(@rewrites, $CONFIG{rew}{$name}{else}{rewrite}[$i]);
					}
				}
				delete $CONFIG{rew}{$name}{else}{rewrite};
				@{$CONFIG{rew}{$name}{else}{rewrite}} = @rewrites;
				if ($oldval =~ /^(log|within|outside)/) {
					delete $CONFIG{rew}{$name}{else}{$1};
				}
			} else {
				for (my $i = 0; $i <= $#{$CONFIG{rew}{$name}{rewrite}}; $i++) {
					if ($CONFIG{rew}{$name}{rewrite}[$i] ne $oldval) {
						
						push(@rewrites, $CONFIG{rew}{$name}{rewrite}[$i]);
					}
				}
				delete $CONFIG{rew}{$name}{rewrite};
				@{$CONFIG{rew}{$name}{rewrite}} = @rewrites;
				if ($oldval =~ /^(log|within|outside)/) {
					delete $CONFIG{rew}{$name}{$1};
				}
			}
		} else {
			if ($else) {
				delete $CONFIG{rew}{$name}{else};
			} else {
				delete $CONFIG{rew}{$name};
			}
		}
		if (!exists $CONFIG{rew}{$name}{within} && !exists $CONFIG{rew}{$name}{outside}) {
			delete $CONFIG{rew}{$name}{else};
		}
		$ACTION = 'rewrites';
	}

	# Update Source addresses\n";
	if ($CGI->param('src')) {
		my $name = $CGI->param('src') || '';
		my $else = $CGI->param('else') || '';
		($name) = &normalyze($name);
		my $type = $CGI->param('srctype') || '';
		my $srcval = $CGI->param('srcval') || '';
		my $oldval = $OLD;
		my $anonymous = $CGI->param('anonymous') || '';
		$oldval = '' if ($oldval =~ /^(log|within|outside) $/);
		if ($oldval) {
			my ($key, $val) = split(/\s/, $oldval, 2);
			if (grep(/^$key$/, @SRC_KEYWORD)) {
				$val = quotemeta($val);
				if ($else) {
					@{$CONFIG{src}{$name}{else}{$key}} = grep(!/^$val$/, @{$CONFIG{src}{$name}{else}{$key}});
				} else {
					@{$CONFIG{src}{$name}{$key}} = grep(!/^$val$/, @{$CONFIG{src}{$name}{$key}});
				}
			} else {
				if ($else) {
					delete $CONFIG{src}{$name}{else}{$key};
				} else {
					delete $CONFIG{src}{$name}{$key};
				}
			}
		}
		if ($srcval) {
			if (grep(/^$type$/, @SRC_KEYWORD)) {
				if ($else) {
					push(@{$CONFIG{src}{$name}{else}{$type}}, "$srcval");
				} else {
					push(@{$CONFIG{src}{$name}{$type}}, "$srcval");
				}
			} elsif ($type eq 'log') {
				$srcval = 'anonymous ' . $srcval if ($anonymous eq 'on');
				if ($else) {
					$CONFIG{src}{$name}{else}{$type} = $srcval;
				} else {
					$CONFIG{src}{$name}{$type} = $srcval;
				}
			} elsif ($type eq 'time') {
				delete $CONFIG{src}{$name}{within};
				delete $CONFIG{src}{$name}{outside};
				($type, $srcval) = split(/[\s\t]+/, $srcval, 2);
				$CONFIG{src}{$name}{$type} = $srcval;
			}
		}
		if (!exists $CONFIG{src}{$name}{within} && !exists $CONFIG{src}{$name}{outside}) {
			delete $CONFIG{src}{$name}{else};
		}
		$ACTION = 'sources';

	} elsif ($CGI->param('source')) {

		my $name = $CGI->param('source') || '';
		my $else = $CGI->param('else') || '';
		($name, $else) = &normalyze($name);
		my $oldval = $OLD;
		$oldval = '' if ($oldval =~ /^(log|within|outside) $/);
		if ($oldval) {
			my ($key, $val) = split(/\s/, $oldval, 2);
			if (grep(/^$key$/, @SRC_KEYWORD)) {
				$val = quotemeta($val);
				if ($else) {
					@{$CONFIG{src}{$name}{else}{$key}} = grep(!/^$val$/, @{$CONFIG{src}{$name}{else}{$key}});
				} else {
					@{$CONFIG{src}{$name}{$key}} = grep(!/^$val$/, @{$CONFIG{src}{$name}{$key}});
				}
			} else {
				if ($else) {
					delete $CONFIG{src}{$name}{else}{$key};
				} else {
					delete $CONFIG{src}{$name}{$key};
				}
			}
		} else {
			if ($else) {
				delete $CONFIG{src}{$name}{else};
			} else {
				delete $CONFIG{src}{$name};
			}
		}
		if (!exists $CONFIG{src}{$name}{within} && !exists $CONFIG{src}{$name}{outside}) {
			delete $CONFIG{src}{$name}{else};
		}
		$ACTION = 'sources';
	}

	# Update destination classes
	if ($CGI->param('category')) {
		my $name = $CGI->param('category') || '';
		my $else = $CGI->param('else') || '';
		my $tmp = '';
		($name, $tmp) = &normalyze($name);
		$else = $tmp if ($tmp);
		if ($ACTION ne 'categoriesdelete') {
			my $time = $CGI->param('time') || '';
			my $domain = $CGI->param('domainlist') || '';
			my $url = $CGI->param('urllist') || '';
			my $expression = $CGI->param('expressionlist') || '';
			my $redirect = $CGI->param('redirect') || '';
			my $log = $CGI->param('log') || '';
			my $anon = $CGI->param('anonymous') || '';
			delete $CONFIG{dest}{$name}{within};
			delete $CONFIG{dest}{$name}{outside};
			if ($time) {
				$time =~ /^(within|outside) (.*)/;
				$CONFIG{dest}{$name}{$1} = $2;
			}
			if (!$else) {
				if ($domain) {
					$CONFIG{dest}{$name}{domainlist} = $domain;
				} else {
					delete $CONFIG{dest}{$name}{domainlist};
				}
				if ($url) {
					$CONFIG{dest}{$name}{urllist} = $url;
				} else {
					delete $CONFIG{dest}{$name}{urllist};
				}
				if ($expression) {
					$CONFIG{dest}{$name}{expressionlist} = $expression;
				} else {
					delete $CONFIG{dest}{$name}{expressionlist};
				}
				if ($redirect) {
					$CONFIG{dest}{$name}{redirect} = $redirect;
				} else {
					delete $CONFIG{dest}{$name}{redirect};
				}
				if ($log) {
					$anon = 'anonymous ' if ($anon);;
					$CONFIG{dest}{$name}{log} = $anon . $log;
				} else {
					delete $CONFIG{dest}{$name}{log};
				}
			} else {
				if ($domain) {
					$CONFIG{dest}{$name}{else}{domainlist} = $domain;
				} else {
					delete $CONFIG{dest}{$name}{else}{domainlist};
				}
				if ($url) {
					$CONFIG{dest}{$name}{else}{urllist} = $url;
				} else {
					delete $CONFIG{dest}{$name}{else}{urllist};
				}
				if ($expression) {
					$CONFIG{dest}{$name}{else}{expressionlist} = $expression;
				} else {
					delete $CONFIG{dest}{$name}{else}{expressionlist};
				}
				if ($redirect) {
					$CONFIG{dest}{$name}{else}{redirect} = $redirect;
				} else {
					delete $CONFIG{dest}{$name}{else}{redirect};
				}
				if ($log) {
					$anon = 'anonymous ' if ($anon);;
					$CONFIG{dest}{$name}{else}{log} = $anon . $log;
				} else {
					delete $CONFIG{dest}{$name}{else}{log};
				}
			}
		} else {
			if (!$else) {
				delete $CONFIG{dest}{$name};
			} else {
				delete $CONFIG{dest}{$name}{else};
			}
		}
		if ($CGI->param('default')) {
			$ACTION = 'bledit';
			$BL = $CGI->param('default');
		} else {
			$ACTION = 'categories';
		}
	}

	# Update Policies
	if ($CGI->param('acl')) {
		my $name = $CGI->param('acl') || '';
		$name =~ s/[^a-z0-9\-\_]//ig;
		if ($ACTION ne 'aclsdelete') {
			delete $CONFIG{acl}{$name}{pass};
			delete $CONFIG{acl}{$name}{else}{pass};
			my @dests = $CGI->param('dest');
			my $all = 1;
			$all = 0 if (!grep(/^all$/, @dests));
			my $none = 0;
			$none = 1 if (grep(/^none$/, @dests));
			push(@{$CONFIG{acl}{$name}{'pass'}}, grep(!/^(all|none)$/, @dests)) if ($#dests >= 0);
			push(@{$CONFIG{acl}{$name}{'pass'}}, 'all') if ($all);
			push(@{$CONFIG{acl}{$name}{'pass'}}, 'none') if ($none && !$all);
			my @edests = $CGI->param('edest');
			$all = 1;
			$none = 0;
			$all = 0 if (!grep(/^all$/, @edests));
			$none = 1 if (grep(/^none$/, @edests));
			push(@{$CONFIG{acl}{$name}{else}{'pass'}}, grep(!/^(all|none)$/, @edests)) if ($#edests >= 0);
			push(@{$CONFIG{acl}{$name}{else}{'pass'}}, 'all') if ($all);
			push(@{$CONFIG{acl}{$name}{else}{'pass'}}, 'none') if ($none && !$all);
			delete $CONFIG{acl}{$name}{'rewrite'};
			delete $CONFIG{acl}{$name}{else}{'rewrite'};
			my @rews = $CGI->param('rew');
			push(@{$CONFIG{acl}{$name}{'rewrite'}}, @rews) if ($#rews >= 0);
			@rews = $CGI->param('erew');
			push(@{$CONFIG{acl}{$name}{else}{'rewrite'}}, @rews) if ($#rews >= 0);
			my $redirect = $CGI->param('redirect') || '';
			delete $CONFIG{acl}{$name}{redirect};
			$CONFIG{acl}{$name}{redirect} = $redirect if ($redirect);
			$redirect = $CGI->param('eredirect') || '';
			delete $CONFIG{acl}{$name}{else}{redirect};
			$CONFIG{acl}{$name}{else}{redirect} = $redirect if ($redirect);
			my $log = $CGI->param('log') || '';
			delete $CONFIG{acl}{$name}{log};
			$CONFIG{acl}{$name}{log} = $log if ($log);
			$log = $CGI->param('elog') || '';
			delete $CONFIG{acl}{$name}{else}{log};
			$CONFIG{acl}{$name}{else}{log} = $log if ($log);

			delete $CONFIG{acl}{$name}{extended};
			my $time = $CGI->param('time') || '';
			if ($time) {
				$time =~ /^([^\s]+)\s([^\s]+)$/;
				$CONFIG{acl}{$name}{extended}{$1} = $2;
			}
		} else {
			delete $CONFIG{acl}{$name};
		}
		$ACTION = 'acl';
	}

	$OLD = '';
	foreach ($CGI->param()) {
		$CGI->delete($_);
	}

}

sub get_translation
{
	my $basedir = shift;

	my %translate = ();

	# Read menu file
	if (open(IN, "$basedir/menu.dat")) {
		while (<IN>) {
			chomp;
			s/
//;
			next if (/^#/ || !$_);
			my ($key, $val) = split(/\t+/);
			$translate{$key} = $val;
		}
		close(IN);
	} 
	return %translate;

}

sub translate
{
	my $key = shift;

	return $LANG{$key} || $key;

}

sub normalyze
{

	my $str = shift;

	my $else = '';
	if ($str =~ s/\-(else)$//) {
		$else = $1;
	}
	$str =~ s/[^-_.a-z0-9]+//gi;
	if (&reserved($str)) {
		$str = 'x' . $str;
	}

	return ($str, $else);

}

sub reserved
{
	my $word = shift;

	my @reserved = qw{
acl             fri             outside         sun             urllist
anonymous       friday          pass            sunday          user
date            fridays         redirect        sundays         userlist
dbhome          ip              rew             thu             wed
dest            log             rewrite         thursday        wednesday
destination     logdir          sat             thursdays       wednesdays
domain          logfile         saturday        time            weekly
domainlist      mon             saturdays       tue             within
else            monday          source          tuesday
expressionlist  mondays         src             tuesdays
};

	return 1 if (grep(/^$word$/, @reserved));

	return 0;
}

sub show_log_schedule
{
	my ($type, $elt, $key, $colspan) = @_;

	$colspan = "colspan=\"$colspan\"" if ($colspan);

	my $v = $CONFIG{$type}{$key}{log} || '';
	my $anon = '';
	if ($v =~ s/anonymous[\s\t]+(.*)/$1/) {
		$anon = "(" . &translate('anonymized') . ")";
	}
	if ($v) {
		print "<tr><th>&nbsp;</th><td $colspan><b>", &translate('Log file'), "</b> : ";
	} else {
		print "<tr><th>&nbsp;</th><td $colspan><b>", &translate('No log file'), "</b>";
	}
	print "$v $anon";
	print "</td><th><a href=\"\" onclick=\"document.forms[0].$elt.value='$key'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{$type}{$key}{log}"), "'; document.forms[0].action.value='${elt}sedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
	if ($v) {
		print "<th><a href=\"\" onclick=\"document.forms[0].$elt.value='$key'; document.forms[0].oldvalue.value='", &encode_url("log $CONFIG{$type}{$key}{log}"), "'; document.forms[0].action.value='${elt}sdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
	} else {
		print "<th>&nbsp;</th>\n";
	}
	print "</tr>\n";

	my $sched = '';
	my $label = 'No schedule association';
	if (exists $CONFIG{$type}{$key}{within}) {
		$sched = 'within';
		$label = 'Within schedule';
	} elsif (exists $CONFIG{$type}{$key}{outside}) {
		$sched = 'outside';
		$label = 'Outside schedule';
	}
	print "<tr><th>&nbsp;</th><td $colspan><b>", &translate($label), "</b> $CONFIG{$type}{$key}{$sched}</td>";
	my $prefix = $sched || 'within';
	print "</td><th><a href=\"\" onclick=\"document.forms[0].$elt.value='$key'; document.forms[0].oldvalue.value='", &encode_url("$prefix $CONFIG{$type}{$key}{$sched}"), "'; document.forms[0].action.value='${elt}sedit'; document.forms[0].submit(); return false;\" title=\"", &translate('Edit'), "\">$IMG_EDIT</a></th>";
	if ($sched) {
		print "<th><a href=\"\" onclick=\"document.forms[0].$elt.value='$key'; document.forms[0].oldvalue.value='", &encode_url("$prefix $CONFIG{$type}{$key}{$sched}"), "'; document.forms[0].action.value='${elt}sdelete'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Delete'), "\">$IMG_DELETE</a></th>";
	} else {
		print "<th>&nbsp;</th>\n";
	}
	print "</tr>\n";
}

sub show_editor
{
	my ($type, $path) = @_;

	if (grep(/^$type$/, 'iplist', 'userlist')) {
		$path = "<a href=\"\" onclick=\"window.open('$ENV{SCRIPT_NAME}?action=editfile&path=$path','filewin','scrollbars=yes,status=no,toolbar=no,width=400,height=800,resizable=yes,screenX=1,screenY=1,top=1,left=1'); return false;\" target=\"_new\" style=\"font-weight: normal;\">$path</a>";
	}

	return $path;
}

sub show_filecontent
{
	my $file = shift;
	my $tail = shift;

	print $CGI->header();
	print $CGI->start_html(
		-title  => "$PROGRAM v$VERSION",
		-author => "$AUTHOR",
		-meta   => { 'copyright' => $COPYRIGHT },
		-style  => { -src => $CSS_FILE },
		-script  => { -src => $JS_FILE },
	);

	print $CGI->start_form();
	print "<input type=\"hidden\" name=\"apply\" value=\"\" />\n";
	print "<input type=\"hidden\" name=\"filename\" value=\"$file\" />\n";

	print "<table><tr>\n";

	if (!$file) {
		&error("No file set");
	} else {
		$file = "$CONFIG{dbhome}/$file" if ($file !~ /^\//);
		print "<h2>", &translate('File'), " : $file</h2>\n";
		if (!$tail) {
			if (-e "$file" && not open(IN, "$file")) {
				&error("Can't read file $file: $!");
			} else {
				if ($ACTION eq 'editfile') {
					print "<th align=\"left\">\n";
					print "<textarea name=\"content\" cols=\"47\" rows=\"42\" wrap=\"off\">\n";
					if (-e "$file") {
						while (<IN>) {
							print "$_";
						}
						close(IN);
					}
					print "</textarea>\n";
					print "</th></tr>\n";
					print "<tr><th align=\"center\"></th></tr>\n";
					print "<tr><th><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); window.close(); return false;\"></th></tr>\n";
				} else {
					print "<th align=\"left\" style=\"font-weight: normal;\"><pre>\n";
					while (<IN>) {
						print "$_";
					}
					print "</pre></th></tr>\n";
				}
			}
		} else {
			print "<th align=\"left\" style=\"font-weight: normal;\"><pre>\n";
			print `$TAIL -n $LOG_LINES $file`;
			print "</pre></th></tr>\n";
		}
	}
	print "<tr><th><input type=\"button\" name=\"close\" value=\"", &translate('Close'), "\" onclick=\"window.close(); return false;\"></th></tr></table>\n";
	print $CGI->end_form();
	print $CGI->end_html();
}

sub save_filecontent
{
	my $file = shift;

	my $content = $CGI->param('content') || '';
	$content =~ s/
//gs;
	my @datas = split(/\n+/, $content);
	$content = '';
	map { s/^[\s]+//; s/[\s]+$//; } @datas;
	$file = "$CONFIG{dbhome}/$file" if ($file !~ /^\//);
	if (not open(OUT, ">$file")) {
		&error("Can't read file $file: $!");
	} else {
		foreach my $l (@datas) {
			print OUT "$l\n" if ($l);
		}
		close(OUT);
	}

}

sub create_default_config
{
	if (not open(OUT, ">$CONF_FILE")) {
		$ERROR = "Can't write configuration file $CONF_FILE: $!\n";
		return;
	}
	$DBHOME ||= '/usr/local/squidGuard/db';
	$LOGDIR ||= '/usr/local/squidGuard/logs';
	print OUT "dbhome $DBHOME\n";
	print OUT "logdir $LOGDIR\n";
	print OUT "\n";
	print OUT "time workhours {\n";
        print OUT "\tweekly mtwhf 08:00 - 18:00\n";
	print OUT "}\n\n";
	print OUT "acl {\n";
	print OUT "\tdefault {\n";
	print OUT "\t\tpass none\n";
	my $host = $ENV{SERVER_NAME} || $ENV{SERVER_ADDR} || 'localhost';
	if ($ENV{SERVER_PORT} != 80) {
		$host .= ":" . $ENV{SERVER_PORT};
	}
	print OUT "\t\tredirect http://$host/cgi-bin/blocked?clientaddr=%a+clientname=%n+clientuser=%i+clientgroup=%s+targetgroup=%t+url=%u\n";
	print OUT "\t}\n";
	print OUT "}\n";
	close(OUT);
	$CGI->delete('action');
	$ACTION = '';
}

sub autocreate_filters
{
	# Read configuration from file squidGuard.conf
	%CONFIG = &get_configuration();

	if (not opendir(DIR, $CONFIG{dbhome})) {
		$ERROR = "can't opendir $CONFIG{dbhome}: $!\n";
		return;
	}
	my @dirs = grep { !/^\./ && -d "$CONFIG{dbhome}/$_" && !-l "$CONFIG{dbhome}/$_"} readdir(DIR);
	my $found = 0;
	foreach my $name (@dirs) {
		if (-e "$CONFIG{dbhome}/$name/domains") {
			$CONFIG{dest}{$name}{domainlist} = "$name/domains";
			$found = 1;
		}
		if (-e "$CONFIG{dbhome}/$name/urls") {
			$CONFIG{dest}{$name}{urllist} = "$name/urls";
			$found = 1;
		}
		if (-e "$CONFIG{dbhome}/$name/expressions") {
			$CONFIG{dest}{$name}{expressionlist} = "$name/expressions";
			$found = 1;
		}
	}
	closedir DIR;
	if (!$found) {
		$ERROR = "No blocklists found under: $CONFIG{dbhome}\n";
	}
	$ACTION = 'categories';
	$CGI->param('action', 'categories');
	&save_config();
}

sub rebuild_database
{
	my $bl = shift;

	if ($bl eq 'all') {
		$ERROR = `$SQUIDGUARD -C all`;
	} else {
		$ERROR = `$SQUIDGUARD -C $bl`;
	}
}

sub squidguard_version
{

	return `$SQUIDGUARD -v 2>&1`;
}

sub show_logs
{

	if (not opendir(DIR, $CONFIG{logdir})) {
		$ERROR = "can't opendir $CONFIG{logdir}: $!";
		return;
	}
	my @files = grep { !/^\./ && -f "$CONFIG{logdir}/$_" } readdir(DIR);
	print "<table >\n";
	print "<tr><td colspan=\"2\">", &show_help('logs'), "</td></tr>\n";
	if ($#files == -1) {
		print "<tr><th>", &translate('No log file'), ".</th></tr>\n";
	} else {
		foreach my $name (@files) {
			print "<tr><th size=\"20\" style=\"text-align: right;\">$IMG_LOG</th><th style=\"text-align: left;\"><a href=\"\" onclick=\"window.open('$ENV{SCRIPT_NAME}?action=viewfile&path=$CONFIG{logdir}/$name&tail=1','filewin','scrollbars=yes,status=no,toolbar=no,width=800,height=800,resizable=yes,screenX=1,screenY=1,top=1,left=1'); return false;\" target=\"_new\">$name</a></th></tr>\n";
		}
	}
	print "</table>\n";
	closedir DIR;
}

sub sc_smgr_header
{

	print $CGI->header();
	print $CGI->start_html(
		-title  => "$SC_PROGRAM v$VERSION",
		-author => "$AUTHOR",
		-meta   => { 'copyright' => $COPYRIGHT },
		-style  => { -src => $CSS_FILE },
		-script  => { -src => $JS_FILE },
	);
	print $CGI->start_form();
	print "<input type=\"hidden\" name=\"action\" value=\"squidclamav\" />\n";
	print "<input type=\"hidden\" name=\"lang\" value=\"$LANG\" />\n";
	print "<input type=\"hidden\" name=\"view\" value=\"$VIEW\" />\n";
	print "<input type=\"hidden\" name=\"apply\" value=\"\" />\n";
	print "<input type=\"hidden\" name=\"oldvalue\" value=\"\" />\n";
	print "<table width=\"100%\" class=\"header\"><tr><td class=\"header\"><a href=\"\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}'; return false;\">$IMG_LOGO</a></td><td class=\"header\">\n<hr>\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='globals'; document.forms[0].submit(); return false;\">", &translate('Globals'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='aborts'; document.forms[0].submit(); return false;\">", &translate('Virus Scanning'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='whitelists'; document.forms[0].submit(); return false;\">", &translate('Whitelists'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='trustusers'; document.forms[0].submit(); return false;\">", &translate('Trusted Users'), "</a> |\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='trustclients'; document.forms[0].submit(); return false;\">", &translate('Trusted Clients'), "</a> |\n";
	print "<br><hr>\n";
	print "<a href=\"\" onclick=\"document.forms[0].view.value='dump'; document.forms[0].submit(); return false;\">", &translate('View Configuration'), "</a> | \n";
	print "<a href=\"\" onclick=\"window.open('$ENV{SCRIPT_NAME}?action=squidclamav&view=showlog&path=$CONFIG{logfile}&lang=$LANG','filewin','scrollbars=yes,status=no,toolbar=no,width=850,height=800,resizable=yes,screenX=1,screenY=1,top=1,left=1'); return false;\" target=\"_new\">", &translate('View log'), "</a> |\n" if ($CONFIG{logfile} && -e $CONFIG{logfile});
	if ($SQUIDCLAMAV eq 'c-icap') {
		print "<a href=\"\" onclick=\"document.forms[0].view.value='cicap'; document.forms[0].submit(); return false;\">", &translate('Reload c-icap'), "</a> |\n";
	} elsif ($SQUID_WRAPPER) {
		print "<a href=\"\" onclick=\"document.forms[0].view.value='squid'; document.forms[0].submit(); return false;\">", &translate('Restart Squid'), "</a> |\n";
	}
	print "<a href=\"\" onclick=\"window.close(); return false;\">", &translate('Close'), "</a> |\n" if ($SQUIDGUARD !~ /^(no|off|disable)/i);
	print "<hr>\n";
	print "</td></tr></table>\n";
}

sub sc_create_default_config
{

	if (not open(OUT, ">$SC_CONF_FILE")) {
		my $err_msg = "Can't write configuration file $SC_CONF_FILE: $!";
		$err_msg .= "File grants: " . `ls -la $CONF_FILE` . "<br>\n";
		my $username = getpwuid( $< );
		$err_msg .= "SquidGuardMgr is running under user: $username\n";
		return $err_msg;
	}
	print OUT qq{
#-----------------------------------------------------------------------------
# SquidClamav default configuration file
#
# To know to customize your configuration file, see squidclamav manpage
# or go to http://squidclamav.darold.net/
#
#-----------------------------------------------------------------------------
#
# Global configuration
#
maxsize 5000000
redirect http://$ENV{SERVER_NAME}/cgi-bin/clwarn.cgi
clamd_local /tmp/clamd
timeout 1
logredir 1
dnslookup 1
};

if ($SQUIDCLAMAV ne 'c-icap') {
	print OUT qq{
squid_ip 127.0.0.1
squid_port 3128
logfile /var/log/squid/squidclamav.log
debug 0
stat 0
maxredir 30
useragent Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)
trust_cache 1
};
}
	close(OUT);

	return;
}

sub sc_show_globals
{
	print "<h2>", &translate('Globals configuration'), "</h2>\n";
	print "<table align=\"center\" width=\"80%\">\n";
	if ($SQUIDCLAMAV ne 'c-icap') {
		print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('Squid parameters'), "</b></td></tr>\n";
		print "<tr><th align=\"left\">", &translate('Squid Ip address'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"squid_ip\" value=\"$CONFIG{squid_ip}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Squid port'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"squid_port\" value=\"$CONFIG{squid_port}\"/></th></tr>\n";
		print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	}
	print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('Clamav parameters'), "</b></td></tr>\n";
	print "<tr><th align=\"left\">", &translate('Clamd Unix Socket'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"clamd_local\" value=\"$CONFIG{clamd_local}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Clamd Ip address'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"clamd_ip\" value=\"$CONFIG{clamd_ip}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Clamd port'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"clamd_port\" value=\"$CONFIG{clamd_port}\"/></th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('SquidGuard parameters'), "</b></td></tr>\n";
	print "<tr><th align=\"left\">", &translate('SquidGuard program'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"squidguard\" value=\"$CONFIG{squidguard}\"/></th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><td align=\"left\" colspan=\"2\"><b>", &translate('SquidClamav parameters'), "</b></td></tr>\n";
	print "<tr><th align=\"left\">", &translate('Redirect'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"redirect\" value=\"$CONFIG{redirect}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Log redirection'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"logredir\" value=\"$CONFIG{logredir}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('DNS lookup'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"dnslookup\" value=\"$CONFIG{dnslookup}\"/></th></tr>\n";
	print "<tr><th align=\"left\">", &translate('Maximum scan size'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"maxsize\" value=\"$CONFIG{maxsize}\"/></th></tr>\n";
	if ($SQUIDCLAMAV ne 'c-icap') {
		print "<tr><th align=\"left\">", &translate('Log file'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"logfile\" value=\"$CONFIG{logfile}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Maximum redirect'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"maxredir\" value=\"$CONFIG{maxredir}\"/></th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Log SquidClamav performence'), "</th><th align=\"left\">\n";
		my $sel1 = '';
		my $sel2 = '';
		($CONFIG{stat}) ? $sel2 = 'selected="1"' : $sel1 = 'selected="1"';
		print "<select name=\"stat\">\n";
		print "<option value=\"0\" $sel1>Off</option>\n";
		print "<option value=\"1\" $sel2>On</option>\n";
		print "</select>\n";
		print "</th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Log debug informations'), "</th><th align=\"left\">\n";
		my %labels = (0 => 'Off', 1 => 'Minimum', 2 => 'Detailled', 3 => 'Full');
		print "<select name=\"debug\">\n";
		foreach my $k (sort keys %labels) {
			my $sel = '';
			$sel = 'selected="1"' if ($CONFIG{debug} == $k);
			print "<option value=\"$k\" $sel>$labels{$k}</option>\n";
		}
		print "</select>\n";
		print "</th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Trust Squid cache'), "</th><th align=\"left\">";
		$sel1 = '';
		$sel2 = '';
		($CONFIG{trust_cache}) ? $sel2 = 'selected="1"' : $sel1 = 'selected="1"';
		print "<select name=\"trust_cache\">\n";
		print "<option value=\"0\" $sel1>Off</option>\n";
		print "<option value=\"1\" $sel2>On</option>\n";
		print "</select>\n";
		print "</th></tr>\n";
		print "<tr><th align=\"left\">", &translate('Change User Agent'), "</th><th align=\"left\"><input type=\"text\" size=\"50\" name=\"useragent\" value=\"$CONFIG{useragent}\"/></th></tr>\n";
	}
	print "<tr><th align=\"left\">", &translate('SquidClamav internal timeout'), "</th><th align=\"left\"><input type=\"text\" size=\"40\" name=\"timeout\" value=\"$CONFIG{timeout}\"/></th></tr>\n";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";

}

sub squidclamav_version
{
	if ($SQUIDCLAMAV eq 'c-icap') {
		return "SquidClamav v6.x";
	}
	return `$SQUIDCLAMAV -v 2>&1`;
}

sub sc_get_configuration
{
	my %infos = ();

	if (not open(IN, $SC_CONF_FILE)) {
		$ERROR = "Can't open configuration file $SC_CONF_FILE: $!\n";
		return;
	}
	while (my $l = <IN>) {
		chomp($l);
		$l =~ s/\#.*//;
		$l =~ s/^[\s\t]+//;
		$l =~ s/[\s\t]+$//;
		next if (!$l);
		my ($key, $val) = split(/[\s\t]+/, $l, 2);
		if ( ($key eq 'abort') || ($key eq 'abortcontent') ) {
			push(@{$infos{$key}}, $val);
		} elsif ( ($key eq 'whitelist') ) {
			push(@{$infos{$key}}, $val);
		} elsif ( ($key eq 'trustuser') || ($key eq 'trustclient') ) {
			push(@{$infos{$key}}, $val);
		} else {
			$infos{$key} = $val;
		}
	}
	close(IN);

	# Set default values
	if ($SQUIDCLAMAV ne 'c-icap') {
		$infos{squid_ip} = '127.0.0.1' if (!exists $infos{squid_ip});
		$infos{squid_port} = 3128 if (!exists $infos{squid_port});
		$infos{debug} = 0 if (!exists $infos{debug});
		$infos{stat} = 0 if (!exists $infos{stat});
		$infos{maxredir} = 30 if (!exists $infos{maxredir});
		$infos{trust_cache} = 1 if (!exists $infos{trust_cache});
		$infos{useragent} = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)' if (!exists $infos{useragent});
	}
	$infos{logredir} = 1 if (!exists $infos{logredir});
	$infos{dnslookup} = 1 if (!exists $infos{dnslookup});
	$infos{timeout} = 1 if (!exists $infos{timeout});
	$infos{maxsize} = 5000000 if (!exists $infos{maxsize});
	return %infos;
}

sub sc_show_whitelist
{
	print "<h2>", &translate('Whitelists definition'), "</h2>\n";
	print "<table align=\"center\" width=\"100%\">\n";
	print "<tr><th valign=\"top\">\n";
	print "<table align=\"center\">\n";
	my $i = 0;
	for ($i = 0; $i <= $#{$CONFIG{whitelist}}; $i++) {
		my $old = $CONFIG{whitelist}[$i];
		$old =~ s/\\/\\\\/g;
		print "<tr><td><input type=\"text\" size=\"60\" name=\"whitelist$i\" value=\"$CONFIG{whitelist}[$i]\"/></td><th><a href=\"\" onclick=\"document.forms[0].oldvalue.value='", &encode_url($old), "'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove'), "\">$IMG_REMOVE</a></th></tr>";
	}
	print "<tr><td align=\"left\">", &translate('List of domain or host to add'), "</td><th>&nbsp;</th></tr>";
	print "<tr><th align=\"left\"><textarea name=\"whitelist$i\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th><th>&nbsp;</th></tr>";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print "</th><th valign=\"top\" style=\"text-align: left; font-weight: normal;\">\n";
	print &show_help('sc_whitelists');
	print "</th></tr></table>\n";

}

sub error
{
	my $error = shift;

	print "<p><font style=\"color: darkred; background: white;\">ERROR: $error</font></p>\n";

}

sub sc_show_trustuser
{
	print "<h2>", &translate('Trusted Users definition'), "</h2>\n";
	print "<table align=\"center\" width=\"100%\">\n";
        print "<tr><th valign=\"top\">\n";
        print "<table align=\"center\">\n";
	my $i = 0;
	for ($i = 0; $i <= $#{$CONFIG{trustuser}}; $i++) {
		my $old = $CONFIG{trustuser}[$i];
		$old =~ s/\\/\\\\/g;
		print "<tr><td><input type=\"text\" size=\"60\" name=\"trustuser$i\" value=\"$CONFIG{trustuser}[$i]\"/></td><th><a href=\"\" onclick=\"document.forms[0].oldvalue.value='", &encode_url($old), "'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove'), "\">$IMG_REMOVE</a></th></tr>";
	}
	print "<tr><td align=\"left\">", &translate('List of user to add'), "</td><th>&nbsp;</th></tr>";
	print "<tr><th align=\"left\"><textarea name=\"trustuser$i\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th><th>&nbsp;</th></tr>";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print "</th><th valign=\"top\" style=\"text-align: left; font-weight: normal;\">\n";
	print &show_help('sc_trustusers');
	print "</th></tr></table>\n";

}

sub sc_show_trustclient
{
	print "<h2>", &translate('Trusted Clients definition'), "</h2>\n";
	print "<table align=\"center\" width=\"100%\">\n";
        print "<tr><th valign=\"top\">\n";
        print "<table align=\"center\">\n";

	my $i = 0;
	for ($i = 0; $i <= $#{$CONFIG{trustclient}}; $i++) {
		my $old = $CONFIG{trustclient}[$i];
		$old =~ s/\\/\\\\/g;
		print "<tr><td><input type=\"text\" size=\"60\" name=\"trustclient$i\" value=\"$CONFIG{trustclient}[$i]\"/></td><th><a href=\"\" onclick=\"document.forms[0].oldvalue.value='", &encode_url($old), "'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove'), "\">$IMG_REMOVE</a></th></tr>";
	}
	print "<tr><td align=\"left\">", &translate('List of clients to add'), "</td><th>&nbsp;</th></tr>";
	print "<tr><th align=\"left\"><textarea name=\"trustclient$i\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th><th>&nbsp;</th></tr>";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	print "</table>\n";
	print "</th><th valign=\"top\" style=\"text-align: left; font-weight: normal;\">\n";
	print &show_help('sc_trustclients');
	print "</th></tr></table>\n";

}

sub sc_show_abort
{
	print "<h2>", &translate('Control Virus Scanning'), "</h2>\n";
	print "<table align=\"center\" width=\"100%\">\n";
	print "<tr><th valign=\"top\">\n";
	print "<table align=\"center\">\n";
	print "<tr><td colspan=\"2\">", &translate('Disable virus scan following regex in URL'), "</th></tr>\n";
	my $found = 0;
	my $i = 0;
	for ($i = 0; $i <= $#{$CONFIG{abort}}; $i++) {
		my $old = $CONFIG{abort}[$i];
		$old =~ s/\\/\\\\/g;
		print "<tr><td><input type=\"text\" size=\"60\" name=\"abort$i\" value=\"$CONFIG{abort}[$i]\"/></td><th><a href=\"\" onclick=\"document.forms[0].oldvalue.value='", &encode_url($old), "'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove'), "\">$IMG_REMOVE</a></th></tr>";
		$found++;
	}
	print "<tr><th align=\"left\"><textarea name=\"abort$i\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th><th>&nbsp;</th></tr>";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";
	print "<tr><td colspan=\"2\">", &translate('Disable scan following regex in Content-Type'), "</th></tr>\n";
	for ($i = 0; $i <= $#{$CONFIG{abortcontent}}; $i++) {
		my $old = $CONFIG{abortcontent}[$i];
		$old =~ s/\\/\\\\/g;
		print "<tr><td><input type=\"text\" size=\"60\" name=\"abortcontent$i\" value=\"$CONFIG{abortcontent}[$i]\"/></td><th><a href=\"\" onclick=\"document.forms[0].oldvalue.value='", &encode_url($old), "'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\" title=\"", &translate('Remove'), "\">$IMG_REMOVE</a></th></tr>";
		$found++;
	}
	print "<tr><th align=\"left\"><textarea name=\"abortcontent$i\" cols=\"50\" rows=\"5\" wrap=\"off\"></textarea></th><th>&nbsp;</th></tr>";
	print "<tr><th colspan=\"2\"><hr></th></tr>\n";

	if ($found) {
		print "<tr><th colspan=\"2\" align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	} else {
		print "<tr><th align=\"left\"><input type=\"button\" name=\"speed\" value=\"", &translate('Optimize for speed'), "\" onclick=\"document.forms[0].view.value='speed'; document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th><th align=\"right\"><input type=\"button\" name=\"save\" value=\"", &translate('Apply change'), "\" onclick=\"document.forms[0].apply.value='1'; document.forms[0].submit(); return false;\"></th></tr>\n";
	}
	print "</table>\n";
	print "</th><th valign=\"top\" style=\"text-align: left; font-weight: normal;\">\n";
	print &show_help('sc_aborts');
	print "</th></tr></table>\n";

}

sub sc_apply_change
{

	# Update Global variables
	if ($VIEW eq 'globals') {
		foreach my $g (@SC_GLOBALVAR) {
			if (defined $CGI->param($g)) {
				$CONFIG{$g} = $CGI->param($g);
			} else {
				delete $CONFIG{$g};
			}
		}
	}

	# Virus Scan abort and abortcontent
	if ($VIEW eq 'aborts') {
		delete $CONFIG{'abort'};
		delete $CONFIG{'abortcontent'};
		foreach my $p ($CGI->param()) {
			next if ($p !~ /^abort/);
			my $val = $CGI->param($p) || '';
			next if (!$val);
			my $tmp = $val;
			$tmp =~ s/([^\\])\\/$1\\\\/g;
			next if ($OLD && ($tmp eq $OLD));
			push(@{$CONFIG{'abort'}}, $val) if ($p =~ /^abort\d+$/);
			push(@{$CONFIG{'abortcontent'}}, $val) if ($p =~ /^abortcontent\d+$/);
			map { s/([^\\])\//$1\\\//g } @{$CONFIG{'abort'}};
			map { s/([^\\])\//$1\\\//g } @{$CONFIG{'abortcontent'}};
		}
	}

	# Whitelist definitions
	if ($VIEW eq 'whitelists') {
		delete $CONFIG{'whitelist'};
		foreach my $p ($CGI->param()) {
			next if ($p !~ /^whitelist/);
			my $tmp = $CGI->param($p);
			$tmp =~ s/([^\\])\\/$1\\\\/g;
			next if ($OLD && ($OLD eq $tmp));
			push(@{$CONFIG{'whitelist'}}, $CGI->param($p)) if ($p =~ /^whitelist\d+$/);
			map { s/([^\\])\//$1\\\//g } @{$CONFIG{'whitelist'}};
		}
	}

	# Trustuser definitions
	if ($VIEW eq 'trustusers') {
		delete $CONFIG{'trustuser'};
		foreach my $p ($CGI->param()) {
			next if ($p !~ /^trustuser/);
			my $tmp = $CGI->param($p);
			$tmp =~ s/([^\\])\\/$1\\\\/g;
			next if ($OLD && ($OLD eq $tmp));
			push(@{$CONFIG{'trustuser'}}, $CGI->param($p)) if ($p =~ /^trustuser\d+$/);
		}
	}

	# Trustclient definitions
	if ($VIEW eq 'trustclients') {
		delete $CONFIG{'trustclient'};
		foreach my $p ($CGI->param()) {
			next if ($p !~ /^trustclient/);
			my $tmp = $CGI->param($p);
			$tmp =~ s/([^\\])\\/$1\\\\/g;
			next if ($OLD && ($OLD eq $tmp));
			push(@{$CONFIG{'trustclient'}}, $CGI->param($p)) if ($p =~ /^trustclient\d+$/);
		}
	}

}

sub sc_save_config
{

	my $content = &sc_dump_config();

	if (not open(OUT, ">$SC_CONF_FILE")) {
		&error("Can't save configuration to file $SC_CONF_FILE: $!");
		return 0;
	}
	print OUT "$content\n";
	close(OUT);

	return 1;
}

sub sc_dump_config
{

	my $config = '';
	$config .= "# Global variables\n";
	foreach my $g (@SC_GLOBALVAR) {
		$config .= "$g $CONFIG{$g}\n" if (defined $CONFIG{$g} && ($CONFIG{$g} ne ''));
	}

	$config .= "\n# Virus Scan abort based on URL and content type pattern matching\n";
	foreach my $v (@{$CONFIG{'abort'}}) {
		$config .= "abort $v\n" if ($v ne '');
	}
	foreach my $v (@{$CONFIG{'abortcontent'}}) {
		$config .= "abortcontent $v\n" if ($v ne '');
	}

	$config .= "\n# Virus Scan and SquidGuard abort based on whitelisted URL pattern matching\n";
	foreach my $v (@{$CONFIG{'whitelist'}}) {
		$config .= "whitelist $v\n" if ($v ne '');
	}

	$config .= "\n# Virus Scan and SquidGuard abort based on authenticated username\n";
	foreach my $v (@{$CONFIG{'trustuser'}}) {
		$config .= "trustuser $v\n" if ($v ne '');
	}

	$config .= "\n# Virus Scan and SquidGuard abort based on remote client ip address or hostname\n";
	foreach my $v (@{$CONFIG{'trustclient'}}) {
		$config .= "trustclient $v\n" if ($v ne '');
	}

	$config .= "\n";

	return $config;
}

sub sc_show_config
{

	print "<h2>SquidClamav configuration</h2>\n";
	print "<table align=\"center\" width=\"80%\">\n";
	print "<tr><th align=\"left\">File: $SC_CONF_FILE</th></tr>\n";
	print "<tr><th><hr /></th></tr>\n";
	print "<tr><th  align=\"left\"><pre>\n";

	print &sc_dump_config();

	print "</pre></td></tr>\n";
	print "</table>\n";

}

sub read_sgm_config
{
	if (not open(IN, "$SGM_CONF")) {
		# We will use default values
		return;
	} else {
		while (my $l = <IN>) {
			chomp($l);
			$l =~ s/
//;
			$l =~ s/[\s\t]*\#.*//;
			next if (!$l);
			my ($key, $val) = split(/[\s\t]+/, $l, 2);
			$key = uc($key);
			${$key} = $val if ($val);
		}
		close(IN);
	}
}

sub show_help
{
	my $type = shift;

	my $helpstr = '';

	if (-e "$LANGDIR/$LANG/$type.html") {
		if (open(IN, "$LANGDIR/$LANG/$type.html")) {
			$helpstr .= $_ while (<IN>);
			close IN;
		}
	} 

	return $helpstr;
}

sub search_database
{
	my $str = shift;
	return if (!$str);

	my @result = `$FIND $CONFIG{dbhome} -type f \\( -name 'domains' -o -name 'urls' \\) -exec $GREP -Hn '$str' '\{\}' \\;`;
	if ($#result >= 0) {
		map { s#$CONFIG{dbhome}\/## } @result;
		map { s#:(\d+):# :Line $1: # } @result;
	} else {
		push(@result, &translate('No data found'));
	}

	return "<pre style=\"color: black;\">" . join('', @result) . "</pre>";
}

sub save_blacklist_description
{
	my $bl = $CGI->param('blacklist') || '';
	my $alias = $CGI->param('alias') || '';
	my $description = $CGI->param('description') || '';

	chomp($alias);
	chomp($description);

	my %bldesc = &get_blacklists_description();
	$bldesc{$bl}{alias} = $alias;
	$bldesc{$bl}{description} = $description;
	if (not open(OUT, ">$LANGDIR/$LANG/$BLDESC")) {
		$ERROR = "Can't open blacklists description $LANGDIR/$LANG/$BLDESC: $!\n";
		return;
	}
	foreach my $l (sort keys %bldesc) {
		print OUT "$l\t";
		print OUT "$bldesc{$l}{alias}\t" if ($bldesc{$l}{alias});
		print OUT "$bldesc{$l}{description}\n";
	}
	close(OUT);

}

sub encode_url
{
	my $bytes = shift;

	chomp($bytes);

	return $bytes if (!$bytes);

	return $CGI->escape($bytes);
}

sub decode_url
{
	my $string = shift;

	return $CGI->unescape($string);

}

sub acl_in_use
{
	my $blname = shift;

	my $found = 0;

	foreach my $d (keys %{$CONFIG{dest}}) {
		if (grep(/^$blname\/(domains|expressions|urls)$/, $CONFIG{dest}{$d}{'domainlist'},
				$CONFIG{dest}{$d}{else}{'domainlist'},
				$CONFIG{dest}{$d}{'expressionlist'},
				$CONFIG{dest}{$d}{else}{'expressionlist'},
				$CONFIG{dest}{$d}{'urllist'},
				$CONFIG{dest}{$d}{else}{'urllist'})
		) {
			$found = 1;
			last;
		}
	}
	return $found;
}

__END__

