VERSION=0.1
RELEASE=1

GROUPS_RPM=test-groups-$(VERSION)-$(RELEASE).noarch.rpm
CONF_RPM=test-configurations-$(VERSION)-$(RELEASE).noarch.rpm

all: groupsrpm confsrpm
PWD=$(shell pwd)

$(GROUPS_RPM): test-groups.spec
	rpmbuild --quiet --define='_topdir $(PWD)/rpm' -bb $<
	cp $(PWD)/rpm/RPMS/noarch/$(GROUPS_RPM) .

$(CONF_RPM): test-configurations.spec
	rpmbuild --quiet --define='_topdir $(PWD)/rpm' -bb $<
	cp $(PWD)/rpm/RPMS/noarch/$(CONF_RPM) .

clean:
	for i in BUILD BUILDROOT RPMS SPECS SRPMS; do rm -rf $(PWD)/rpm/$$i; done
	rm -f $(GROUPS_RPM) $(CONF_RPM)

groupsrpm: $(GROUPS_RPM)
confsrpm: $(CONF_RPM)

.PHONY: groupsrpm confsrpm clean
