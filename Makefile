PSTORE=srv/BOSS/processes
BINDIR=usr/bin
BSDIR=usr/share/boss-skynet
CONFDIR=etc/skynet
COVERAGE := $(shell which python-coverage)
INSTALLEXEC=install -D -m 755
INSTALLCONF=install -D -m 644
INSTALLDIR=install -d -m 744

docs: test_results.txt code_coverage.txt
	cd docs; make coverage
	cd docs; make html

install: dirs participants launchers conf modules utils

dirs:
	$(INSTALLDIR) $(DESTDIR)/$(CONFDIR)
	$(INSTALLDIR) $(DESTDIR)/$(BSDIR)/
	$(INSTALLDIR) $(DESTDIR)/var/run/obsticket
	$(INSTALLDIR) $(DESTDIR)/$(PSTORE)/StandardWorkflow/

conf:
	cd conf ; \
	$(INSTALLCONF) notify.conf      $(DESTDIR)/$(CONFDIR) ; \
	$(INSTALLCONF) getbuildlog.conf $(DESTDIR)/$(CONFDIR) ; \
	$(INSTALLCONF) obsticket.conf   $(DESTDIR)/$(CONFDIR) ; \
	$(INSTALLCONF) test_image.conf  $(DESTDIR)/$(CONFDIR) ; \
	$(INSTALLCONF) bugzilla.conf    $(DESTDIR)/$(CONFDIR) ; \
	$(INSTALLCONF) robogrator.conf  $(DESTDIR)/$(CONFDIR) ; \
	install -D -m 600 oscrc  	    $(DESTDIR)/$(CONFDIR)

modules:
	cd modules/ots ; \
	python setup.py -q install --root=$(DESTDIR) --prefix=$(PREFIX)

launchers:
	cd launchers ; \
	$(INSTALLEXEC) robogrator.py $(DESTDIR)/$(BSDIR)/

participants:
	cd participants ; \
	$(INSTALLEXEC) notify.py                        $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) getbuildlog.py                   $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) get_changelog.py                 $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) get_relevant_changelog.py        $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) obsticket.py                     $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) test_image.py                    $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_already_testing.py         $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_has_valid_repo.py          $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_multiple_destinations.py   $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_no_changes.py              $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_package_built_at_source.py $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_package_is_complete.py     $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_spec.py                    $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_submitter_maintainer.py    $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) get_submitter_email.py           $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_has_relevant_changelog.py  $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_is_from_devel.py           $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) change_request_state.py          $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) do_build_trial.py                $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) do_revert_trial.py               $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) get_build_trial_results.py       $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) is_repo_published.py             $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) bz.py                            $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) check_mentions_bug.py            $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) built_notice.py                  $(DESTDIR)/$(BSDIR)/ ; \
	$(INSTALLEXEC) standard_workflow_handler.py     $(DESTDIR)/$(BSDIR)/

utils:
	cd utils ; \
	$(INSTALLEXEC) boss_swf_enable $(DESTDIR)/$(BINDIR)/ ; \
	$(INSTALLEXEC) platform_setup  $(DESTDIR)/$(BINDIR)/

processes:
	cd processes ; \
	$(INSTALLEXEC) BOSS_handle_SR      $(DESTDIR)/$(PSTORE)/StandardWorkflow/BOSS_handle_SR ; \
	$(INSTALLEXEC) trial_build_monitor $(DESTDIR)/$(PSTORE)/StandardWorkflow/trial_build_monitor

test_results.txt:
	PYTHONPATH=participants:launchers:modules \
	nosetests -v --with-coverage --cover-package participants,launchers,modules \
	--cover-inclusive 2> test_results.txt \
		&& cat test_results.txt \
		|| (cat test_results.txt; exit 1)

code_coverage.txt: test_results.txt
ifdef COVERAGE
	$(COVERAGE) -rm participants/*.py launchers/*.py modules/ots/*.py 2>&1 | tee code_coverage.txt
else
	@echo "Coverage not available" > code_coverage.txt
endif

.test_stamp: test_results.txt
	touch .test_stamp

faketest:
	@echo "Tests not run" > test_results.txt
	@echo "Coverage not available" > code_coverage.txt
	touch .test_stamp

test: .test_stamp

clean:
	@rm -rf docs/_build
	@rm -f .coverage participants/*.pyc launchers/*.pyc code_coverage.txt \
		test_results.txt .test_stamp docs/c.txt docs/python.txt \
		docs/undoc.pickle tests/*.pyc .noseids

.PHONY: dirs docs install clean test faketest participants launchers conf modules utils
all: docs
