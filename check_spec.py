#!/usr/bin/python
""" Quality check participant """

import sys, traceback
#import tempfile
from buildservice import BuildService

try:
    import json
except ImportError:
    import simplejson as json

#def getSectionOrTag(spec, tag):
#    """
#      Reuse function from osc/core.py line 3055
#    """
#    try:
#        specfile = tempfile.NamedTemporaryFile(delete=False)
#        specfile.write(spec)
#        specfile.close()
#        d = read_meta_from_spec(specfile.name, tag)
#        return d[tag]
#    finally:
#        os.remove(specfile.name)


def hasSectionOrTag(spec, tag):
    """ simple check function that is faster than the one above
        and doesn't use temporary files """
    return tag in spec


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
    
    def getSpecFile(self, prj, pkg, rev=None):

        """ Get a package's spec file """

        spec = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".spec"):
                spec = self.obs.getFile(prj, pkg, fil)
        return spec

    def specValid(self, prj, pkg, revision):
        """
          Get spec file and check for various indications of spec file validity
        """
        result = True
        msg = []
        spec = self.getSpecFile(prj, pkg, revision)

        if hasSectionOrTag(spec, "%changelog"):
            result = False
            msg.append("Spec file for package %s should not contain the \
                        %%changelog tag, otherwise the changes file is \
                        ignored" % pkg)
        return result, msg

    def quality_check(self, wid):

        """ Quality check implementation """

        result = True
        msg = [] if not wid.lookup("msg") else wid.lookup("msg")
        actions = wid.lookup('actions')
        #project = wid.lookup('project')
        #repository = wid.lookup('repository')
        #targetrepo = wid.lookup('target_repo')
        #archs = wid.lookup('archs')
        #archstring = ", ".join(archs)

        for action in actions:
            # Assert validity of spec file
            valid , mesg = self.specValid(action['sourceproject'],
                                          action['sourcepackage'],
                                          action['sourcerevision'])
            if not valid:
                msg.extend(mesg)
                wid.set_field("status","FAILED")
                result = False

        if result :
            msg.append("Spec files valid.")

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

