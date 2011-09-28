NAME=test-groups
VERSION=0.1
RELEASE=1

TARFILE=rpm/SOURCES/$(NAME)_$(VERSION).orig.tar.gz
RPMFILE=$(NAME)-$(VERSION)-$(RELEASE).noarch.rpm

all: groupsrpm

$(TARFILE): testpattern.xml
	mkdir -p $(PWD)/rpm/SOURCES
	tar cfz $(PWD)/$@ $<

$(RPMFILE): test-groups.spec $(TARFILE)
	rpmbuild --quiet --define='_topdir $(PWD)/rpm' -bb $<
	cp $(PWD)/rpm/RPMS/noarch/$(RPMFILE) .

clean:
	rm -rf $(PWD)/rpm
	rm -f $(RPMFILE)

groupsrpm: $(RPMFILE)

.PHONY: groupsrpm clean
