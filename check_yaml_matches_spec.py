#!/usr/bin/python
""" If a yaml file is present, check that running spectacle on it
reproduces the spec.

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.

:term:`Workitem` fields OUT

:Returns:
    result(Boolean):
       True if yaml matches the spec file, False otherwise.

"""
from buildservice import BuildService

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def getSpecYamlFiles(self, prj, pkg, rev=None):

        """ Get a package's spec and yaml filenames """

        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".spec"):
                spec = self.obs.getFile(prj, pkg, fil)
            if fil.endswith(".yaml"):
                yaml = self.obs.getFile(prj, pkg, fil)
        return spec, yaml

    def SpecMatchesYaml(self, spec, yaml):
        """
          Takes the filenames of a spec and yaml file.
          Creates a temporary spec from the yaml.
          Returns True if there is no yaml
          Returns True if spec matches yaml
          Returns False if there is a yaml but it doesn't match the spec
        """
        msg = []
        if yaml == None:
            return True

        # Run specify
        # compare result

        return False, msg

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        wid.result = False

        self.setup_obs(wid.fields.ev.namespace)

        if not wid.fields.msg:
            wid.fields.msg = []

        actions = wid.fields.ev.actions
        if not actions:
            wid.fields.__error__ = "Mandatory field: actions does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        result = True

        for action in actions:
            # Assert validity of spec file
            spec, yaml = self.getSpecYamlFiles(action['sourceproject'],
                                               action['sourcepackage'],
                                               action['sourcerevision'])
            # We only check the equivalence if a yaml is provided
            if yaml:
                valid , msg = self.SpecMatchesYaml(spec, yaml)
                if not valid:
                    wid.fields.msg.extend(msg)
                    result = False

        wid.result = result
