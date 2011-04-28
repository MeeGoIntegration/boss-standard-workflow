default:
	touch default

install:
	install -D -m 755 check_already_testing.py          $(DESTDIR)/usr/share/boss-skynet/check_already_testing.py
	install -D -m 755 check_has_valid_repo.py           $(DESTDIR)/usr/share/boss-skynet/check_has_valid_repo.py
	install -D -m 755 check_multiple_destinations.py    $(DESTDIR)/usr/share/boss-skynet/check_multiple_destinations.py
	install -D -m 755 check_no_changes.py               $(DESTDIR)/usr/share/boss-skynet/check_no_changes.py
	install -D -m 755 check_package_built_at_source.py  $(DESTDIR)/usr/share/boss-skynet/check_package_built_at_source.py
	install -D -m 755 check_package_is_complete.py      $(DESTDIR)/usr/share/boss-skynet/check_package_is_complete.py
	install -D -m 755 check_spec.py                     $(DESTDIR)/usr/share/boss-skynet/check_spec.py
	install -D -m 755 check_submitter_maintainer.py     $(DESTDIR)/usr/share/boss-skynet/check_submitter_maintainer.py
	install -D -m 755 get_submitter_email.py            $(DESTDIR)/usr/share/boss-skynet/get_submitter_email.py
	install -D -m 755 check_has_relevant_changelog.py   $(DESTDIR)/usr/share/boss-skynet/check_has_relevant_changelog.py

