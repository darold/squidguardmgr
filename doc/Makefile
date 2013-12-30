SHELL = /bin/sh
POD2MAN = /usr/bin/pod2man
POD2TXT = /usr/bin/pod2text
PODSRC = squidguardmgr.pod
MMAN = squidguardmgr.3
TREADME = ../README
TINSTALL = ../INSTALL
OUTFILES = $(MMAN) $(TREADME) $(TINSTALL)

.PHONY: all clean

all: clean $(OUTFILES)

$(MMAN): $(PODSRC)
	$(POD2MAN) $< $@

$(TREADME): $(PODSRC)
	$(POD2TXT) $< $@

$(TINSTALL): $(PODSRC)
	$(POD2TXT) $< $@
	perl -i -pe 'BEGIN {undef $$/;} s/\nFEATURES\n.*?(\nREQUIREMENT)/$$1/s;' $@
	perl -i -pe 'BEGIN {undef $$/; $$r="    See README file.\n";} s/(\nCONFIGURATION\n).*?(\nAUTHORS)/$$1$$r$$2/s;' $@

clean:
	-rm -f $(OUTFILES)
