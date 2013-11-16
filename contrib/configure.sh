#!/bin/sh

perl Makefile.PL \
 CONFFILE=/etc/squid/squidGuard.conf \
 DBHOME=/var/squidGuard/blacklist \
 LOGDIR=/var/log/httpd/squidGuard \
 WWWDIR=/var/www/sgmgr \
 LANGDIR=en_US \
 BASEURL=/squidguardmgr \
 SQUIDUSR=squid SQUIDGRP=squid

# Make squidguardmgr httpd process's DocumentRoot and log directory.
sudo mkdir -p /var/www/squid-gui
sudo mkdir -p /var/log/httpd/squidguardmgr
