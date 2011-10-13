PSTORE=srv/BOSS/processes
TSTORE=srv/BOSS/templates
KSSTORE=srv/BOSS/kickstarts
BINDIR=usr/bin
BSDIR=usr/share/boss-skynet
CONFDIR=etc/skynet
COVERAGE := $(shell which python-coverage)
INSTALLEXEC=install -D -m 755
INSTALLCONF=install -D -m 644
INSTALLDIR=install -d -m 744
POBJECTS := $(wildcard participants/*.py)
LOBJECTS := $(wildcard launchers/*.py)
COBJECTS := $(wildcard conf/*.conf)
MOBJECTS := $(shell find modules/* -maxdepth 0 -type d -exec basename \{\} \;)
PYSETUPOPT := --install-layout=deb

docs: test_results.txt code_coverage.txt
	cd docs; make coverage
	touch docs/metrics.rst
	cd docs; make html

install: dirs participants launchers conf modules utils processes templates kickstarts

dirs:
	$(INSTALLDIR) $(DESTDIR)/$(CONFDIR)
	$(INSTALLDIR) $(DESTDIR)/$(BINDIR)
	$(INSTALLDIR) $(DESTDIR)/$(BSDIR)/
	$(INSTALLDIR) $(DESTDIR)/var/run/obsticket
	$(INSTALLDIR) $(DESTDIR)/$(PSTORE)/StandardWorkflow/
	$(INSTALLDIR) $(DESTDIR)/$(TSTORE)/
	$(INSTALLDIR) $(DESTDIR)/$(KSSTORE)/

conf:
	@for C in $(COBJECTS); do \
	    echo $(INSTALLCONF) $$C $(DESTDIR)/$(CONFDIR)/ ; \
	    $(INSTALLCONF) $$C $(DESTDIR)/$(CONFDIR)/ ; \
	done

modules:
	cd modules ; \
	python setup.py -q install --root=$(DESTDIR) $(PYSETUPOPT)

launchers:
	@for L in $(LOBJECTS); do \
	    echo $(INSTALLEXEC) $$L $(DESTDIR)/$(BSDIR)/ ; \
	    $(INSTALLEXEC) $$L $(DESTDIR)/$(BSDIR)/ ; \
	done

participants:
	@for P in $(POBJECTS); do \
	    echo $(INSTALLEXEC) $$P $(DESTDIR)/$(BSDIR)/ ; \
	    $(INSTALLEXEC) $$P $(DESTDIR)/$(BSDIR)/ ; \
	done

utils:
	cd utils ; \
	$(INSTALLEXEC) boss_swf_enable $(DESTDIR)/$(BINDIR)/ ; \
	$(INSTALLEXEC) platform_setup  $(DESTDIR)/$(BINDIR)/

processes:
	cd processes ; \
	$(INSTALLCONF) SRCSRV_REQUEST_CREATE.BOSS_handle_SR.pdef      $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	$(INSTALLCONF) SRCSRV_REQUEST_STATECHANGE.BOSS_handle_SR.pdef $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	$(INSTALLCONF) SRCSRV_REQUEST_CREATE.BOSS_handle_SR.conf $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	$(INSTALLCONF) trial_build_monitor $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	$(INSTALLCONF) REPO_PUBLISH.BOSS_update_REVS.pdef    $(DESTDIR)/$(PSTORE)/StandardWorkflow/

templates:
	cd templates ; \
	$(INSTALLEXEC) submit_request_bz $(DESTDIR)/$(TSTORE)/ ; \
	$(INSTALLEXEC) submit_request_email $(DESTDIR)/$(TSTORE)/

kickstarts:
	cd kickstarts ; \
	$(INSTALLEXEC) meego-core-ia32-minimal.ks $(DESTDIR)/$(KSSTORE)/

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
	@find -name "*.pyc" -delete
	@rm -f .coverage code_coverage.txt test_results.txt \
	    .test_stamp docs/c.txt docs/python.txt docs/undoc.pickle \
	    .noseids
	@cd modules; python setup.py -q clean --all >/dev/null 2>/dev/null

.PHONY: dirs docs install clean test faketest participants launchers conf modules utils processes templates kickstarts
all: docs
