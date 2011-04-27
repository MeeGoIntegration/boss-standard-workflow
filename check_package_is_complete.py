#!/usr/bin/python
""" Quality check participant """

import sys, traceback
from buildservice import BuildService

try:
    import json
except ImportError:
    import simplejson as json

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = BuildService()

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass
    
    def isComplete(self, prj, pkg, revision):

        """ Package file completeness check """

        filelist = self.obs.getPackageFileList(prj, pkg, revision)
        specfile = changesfile = sourcefile = False
        for fil in filelist:
            sourcefile = True if fil.endswith(".tar.bz2") \
                              or fil.endswith(".tar.gz")  \
                              or fil.endswith(".tgz")     \
                              or sourcefile                \
                              else False
            changesfile = True if fil.endswith(".changes") \
                          or changesfile                    \
                          else False
            specfile = True if fil.endswith(".spec") \
                            or specfile               \
                            else False
        return sourcefile and changesfile and specfile

    def quality_check(self, wid):

        """ Quality check implementation """

        result = True
        msg = [] if not wid.lookup("msg") else wid.lookup("msg")
        actions = wid.lookup('actions')
        #project = wid.lookup('project')
        #repository = wid.lookup('repository')
        #targetrepo = wid.lookup('targetrepo')
        #archs = wid.lookup('archs')
        #archstring = ", ".join(archs)

        for action in actions:
            # Assert needed files are there.
            if not self.isComplete(action['sourceproject'],
                                   action['sourcepackage'],
                                   action['sourcerevision']):
                wid.set_field("status","FAILED")
                msg.append("Package %s in project %s missing files. At least \
                            compressed source tarball, .spec and .changes \
                            files should be present" % (action['sourcepackage'],
                                                       action['sourceproject']))
                result = False


        if result :
            msg.append("Packages in request contain all mandatory files.")

        wid.set_field("msg", msg)
        wid.set_result(result)

        return wid


    def handle_wi(self, wid):

        """ actual job thread """

        try:
            # We may want to examine the fields structure
            if 'debug_dump' in wid.fields():
                print json.dumps(wid.to_h(), sort_keys=True, indent=4)

            wid = self.quality_check(wid)

        except Exception as exp :
            print "Failed with exceptions %s " % exp
            wid.set_field("status","FAILED")
            traceback.print_exc(file=sys.stdout)
            wid.set_result(False)
        finally:
            print "Request #%s %s:\n%s" % (wid.lookup('rid'),
                                           wid.lookup('status'),
                                           "\n".join(wid.lookup('msg')))

