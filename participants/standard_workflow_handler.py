#!/usr/bin/python  # -*- python -*-
#
# The message containers are a minimal requirement
from SkyNET import (WorkItemCtrl, ParticipantCtrl, Workitem)

class ParticipantHandler(object):
    """
    This is the standard_workflow_handler.

    Repositories for an OBS project move between 'published' and
    'building' states. The initial transition is usually caused by a
    package commit.

    Unless special efforts are made, additional package commits may be
    made to the project whilst the build is in progress. These
    packages will be correctly integrated into the final published
    build. However, there is no way to tell from OBS which packages
    were rebuilt and so need testing. This participant handles that by
    tracking which packages are committed (or triggered) and and hence
    need testing next time a project is published and ensures they're
    added to the 'packages' list for a REPO_PUBLISHED.

    Deployment:

    The handler should run as a very early participant on all the followin events:
    * SRCSRV_COMMIT
    * REPO_PUBLISHED
    * BUILD_UNCHANGED
    * BUILD_FAIL
    * BUILD_SUCCESS
    * SRCSRV_VERSION_CHANGE
    * SRCSRV_DELETE_PACKAGE
    * SRCSRV_REQUEST_CREATE

    """

    def __init__(self,*args, **kwargs):
        self.needs_testing = {}
        self.new_packages = {}

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        pass

    def handle_wi(self, wi):

        ev = wi.fields.ev
        if not ev:
	    print "NOEV"
            return

        # We use the event label
        label = ev.label

        # SRCSRV_COMMIT / BUILD_SUCCESS
        # project, package, files, rev, user, comment
        # This is a commit change to a package. It's changed and we
        # flag that it needs testing. This should be a process This
        # needs to be in a DB of some sort for persistence
        # FIXME: iamer: We really nead a way to store transient data
        # in a reliable manner.
        # (Note this was originally used in robogrator for *all*
        # projects)
        if label == "SRCSRV_COMMIT" or (label == "BUILD_SUCCESS"
                                        and wi.fields.test_triggered_packages):
            if ev.project not in self.needs_testing:
                self.needs_testing[ev.project] = {}
            self.needs_testing[ev.project][ev.package] = True
            print "%s / %s needs testing at the next publish" % (ev.project, ev.package)
            wi.fields.package = ev.package
            return

        # REPO_PUBLISHED
        if label == "REPO_PUBLISHED":
            # project, repo
            print "%s is done building .. now to test" % ev.project
            plist = None
            if ev.project in self.needs_testing:
                plist = [x for x in self.needs_testing[ev.project].keys() if self.needs_testing[ev.project][x]]
            else:
                print "No packages to test in %s" % ev.project

            # Clear down the testing list
            self.needs_testing[ev.project] = {}
            if plist and len(plist) > 0:
                wi.fields.packages = plist
                wi.fields.repository = ev.repo
            return

        # BUILD_UNCHANGED
        if label == "BUILD_UNCHANGED":
            print "%s is done building in %s .. but nothing changed" % ( ev.package, ev.project )
            plist = None
            if ev.project in self.needs_testing and ev.package in self.needs_testing[ev.project].keys():
                # Clear down the testing list
                del(self.needs_testing[ev.project][ev.package])
                wi.fields.package = ev.package
            else:
                print "Package was not supposed to be tested in %s" % ev.project
            return

        # BUILD_FAIL
        if label == "BUILD_FAIL":
            if ev.project in self.needs_testing and ev.package in self.needs_testing[ev.project].keys():
                # Clear down the testing list
                del(self.needs_testing[ev.project][ev.package])
                wi.fields.package = ev.package
                return

        # SRCSRV_VERSION_CHANGE
        if label == "SRCSRV_VERSION_CHANGE":
            if ev.project in self.new_packages and ev.package in self.new_packages[ev.project].keys():
                # Clear down the new list
                del(self.new_packages[ev.project][ev.package])
                print "Package %s is new in %s, ignoring version change" % (ev.package , ev.project)
                return
            wi.fields.package = ev.package
            wi.fields.rev = ev.rev
            wi.fields.version = ev.newversion
            return

        # SRCSRV_CREATE_PACKAGE
        if label == "SRCSRV_CREATE_PACKAGE":
            if ev.project not in self.new_packages:
                self.new_packages[ev.project] = {}
            self.new_packages[ev.project][ev.package] = True
            wi.fields.package = ev.package
            return

        # SRCSRV_DELETE_PACKAGE
        if label == "SRCSRV_DELETE_PACKAGE":
            if ev.project in self.needs_testing and ev.package in self.needs_testing[ev.project].keys():
                # Clear down the testing list
                del(self.needs_testing[ev.project][ev.package])
            wi.fields.package = ev.package
            return

        # SRCSRV_REQUEST_*
        # This may contain references for multiple projects
        # however if robogrator sent it here
        if label.startswith("SRCSRV_REQUEST"):
            wi.fields.actions = ev.actions
            wi.fields.who = ev.sender
            wi.fields.rid = ev.id
            wi.fields.description = ev.description
            wi.fields.when = ev.when
            return
