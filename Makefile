PSTORE=/srv/BOSS/processes
BINDIR=/usr/bin

all:
	echo No build required
#docs:
#	cd docs; make html

install:
	install -d $(DESTDIR)/$(PSTORE)/StandardWorkflow/
	install -D -m 755 BOSS_handle_SR         $(DESTDIR)/$(PSTORE)/StandardWorkflow/BOSS_handle_SR
	install -D -m 755 trial_build_monitor    $(DESTDIR)/$(PSTORE)/StandardWorkflow/trial_build_monitor
	install -D -m 755 swf_enable $(DESTDIR)/$(BINDIR)/swf_enable

clean:
	rm -f default
#	rm -rf docs/_build

#.PHONY: docs
