BSDIR=usr/share/boss-skynet

docs:
	cd docs; make html

install:
	install -D -m 755 check_already_testing.py          $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_has_valid_repo.py           $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_multiple_destinations.py    $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_no_changes.py               $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_package_built_at_source.py  $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_package_is_complete.py      $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_spec.py                     $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_submitter_maintainer.py     $(DESTDIR)/$(BSDIR)/
	install -D -m 755 get_submitter_email.py            $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_has_relevant_changelog.py   $(DESTDIR)/$(BSDIR)/
	install -D -m 755 check_is_from_devel.py            $(DESTDIR)/$(BSDIR)/

clean:
	rm -f default
	rm -rf docs/_build

.PHONY: docs
all: docs
