PSTORE=srv/BOSS/processes
TSTORE=srv/BOSS/templates
KSSTORE=srv/BOSS/kickstarts
BINDIR=usr/bin
BSDIR=usr/share/boss-skynet
PCONFDIR=etc/skynet
SCONFDIR=etc/skynet/conf.d
SVDIR=etc/supervisor/conf.d
COVERAGE := $(shell which python-coverage)
INSTALLEXEC=install -D -m 755
INSTALLCONF=install -D -m 644
INSTALLDIR=install -d -m 755
POBJECTS := $(wildcard participants/*.py)
LOBJECTS := $(wildcard launchers/*.py)
PCOBJECTS := $(wildcard conf/*.conf)
SCOBJECTS := $(wildcard conf/skynet/*.conf)
SVOBJECTS := $(wildcard conf/supervisor/*.conf)
MOBJECTS := $(shell find modules/* -maxdepth 0 -type d -exec basename \{\} \;)
TEMPLATEOBJECTS := $(wildcard templates/*)
PROCESSOBJECTS := $(wildcard processes/*.conf processes/*.pdef)

docs: faketest test_results.txt code_coverage.txt
	cd docs; make coverage
	touch docs/metrics.rst
	cd docs; make html

install: dirs participants launchers conf sv modules utils processes templates kickstarts

dirs:
	$(INSTALLDIR) $(DESTDIR)/$(PCONFDIR)
	$(INSTALLDIR) $(DESTDIR)/$(SCONFDIR)
	$(INSTALLDIR) $(DESTDIR)/$(BINDIR)
	$(INSTALLDIR) $(DESTDIR)/$(BSDIR)/
	$(INSTALLDIR) $(DESTDIR)/var/lib/obsticket
	$(INSTALLDIR) $(DESTDIR)/$(PSTORE)/StandardWorkflow/
	$(INSTALLDIR) $(DESTDIR)/$(TSTORE)/
	$(INSTALLDIR) $(DESTDIR)/$(KSSTORE)/
	$(INSTALLDIR) $(DESTDIR)/$(SVDIR)/

conf:
	@for C in $(PCOBJECTS); do \
	    echo $(INSTALLCONF) $$C $(DESTDIR)/$(PCONFDIR)/ ; \
	    $(INSTALLCONF) $$C $(DESTDIR)/$(PCONFDIR)/ ; \
	done
	@for C in $(SCOBJECTS); do \
	    echo $(INSTALLCONF) $$C $(DESTDIR)/$(SCONFDIR)/ ; \
	    $(INSTALLCONF) $$C $(DESTDIR)/$(SCONFDIR)/ ; \
	done

sv:
	@for SV in $(SVOBJECTS); do \
	    echo $(INSTALLCONF) $$SV $(DESTDIR)/$(SVDIR)/ ; \
	    $(INSTALLCONF) $$SV $(DESTDIR)/$(SVDIR)/ ; \
	done

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
	$(INSTALLEXEC) platform_setup  $(DESTDIR)/$(BINDIR)/ ; \
	$(INSTALLEXEC) launcher.py     $(DESTDIR)/$(BINDIR)/ ; \
	$(INSTALLEXEC) repodiff.py     $(DESTDIR)/$(BINDIR)/

processes:
	@for P in $(PROCESSOBJECTS); do \
	    echo $(INSTALLCONF) $$P $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	    $(INSTALLCONF) $$P $(DESTDIR)/$(PSTORE)/StandardWorkflow/ ; \
	done

templates:
	@for T in $(TEMPLATEOBJECTS); do \
	    echo $(INSTALLCONF) $$T $(DESTDIR)/$(TSTORE)/ ; \
	    $(INSTALLCONF) $$T $(DESTDIR)/$(TSTORE)/ ; \
	done

kickstarts:
	cd kickstarts ; \
	$(INSTALLEXEC) meego-core-ia32-minimal.ks $(DESTDIR)/$(KSSTORE)/

test_results.txt:
	PYTHONPATH=participants:launchers:modules:$$PYTHONPATH \
	nosetests -v --with-coverage --cover-package none \
	--cover-inclusive 2> test_results.txt \
		&& cat test_results.txt \
		|| (cat test_results.txt; exit 1)

code_coverage.txt: test_results.txt
ifdef COVERAGE
	$(COVERAGE) -rm participants/*.py\
	    launchers/*.py\
	    modules/ots/*.py\
	    modules/boss/*.py 2>&1 | tee code_coverage.txt
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

retest:
	@rm -f test_results.txt code_coverage.txt .coverage
	$(MAKE) code_coverage.txt

clean:
	@rm -rf docs/_build
	@find -name "*.pyc" -delete
	@rm -f .coverage code_coverage.txt test_results.txt \
	    .test_stamp docs/c.txt docs/python.txt docs/undoc.pickle \
	    .noseids

.PHONY: dirs docs install clean test faketest participants launchers conf modules utils processes templates kickstarts retest sv
all: docs

