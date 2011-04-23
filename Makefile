default:
	touch default

install:
	install -D -m 755 already_testing.py       $(DESTDIR)/usr/share/boss-skynet/already_testing.py
	install -D -m 755 has_changes.py           $(DESTDIR)/usr/share/boss-skynet/has_changes.py
	install -D -m 755 package_complete.py      $(DESTDIR)/usr/share/boss-skynet/package_complete.py
	install -D -m 755 package_successful.py    $(DESTDIR)/usr/share/boss-skynet/package_successful.py
	install -D -m 755 spec_valid.py            $(DESTDIR)/usr/share/boss-skynet/spec_valid.py
	install -D -m 755 target_repo.py           $(DESTDIR)/usr/share/boss-skynet/target_repo.py
	install -D -m 755 submitter_email.py       $(DESTDIR)/usr/share/boss-skynet/submitter_email.py
	install -D -m 755 submitter_maintainer.py  $(DESTDIR)/usr/share/boss-skynet/submitter_maintainer.py
	install -D -m 755 multiple_destinations.py $(DESTDIR)/usr/share/boss-skynet/multiple_destinations.py

