#!/usr/bin/python
""" This participants gets the relevant changelog entries of the packages being
submitted by comparing its changes file to the one in the destination,
OR by comparing the destination changes file to its previous revision.
It then extends the actions array with these results.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` params IN

:Parameters:
   compare(string):
      if "last_revision" the relevant changelog entries will be obtained by
      comparing to the previous revision of the file in the destination.
      Otherwise it compares the changes file from source to the destination.

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if no packages are already in testing, False if a package was already
      found in testing

   ev.actions.relevant_changelog(list):
      Extends the submit request data structure :term:`actions` with the
      relevant_changelog field which contains a list of changelog entries

"""


import difflib
import re
from buildservice import BuildService
from urllib2 import HTTPError

_blankre = re.compile(r"^\W*$")

def get_relevant_changelog(src_chlog, dst_chlog):
    """ Diff two changelogs and return the list of lines that are only in
        the source changelog """

    relchlog = []
    # compare source changelog to dest changelog
    if not src_chlog:
        # If source is empty, do nothing
        pass
    elif not dst_chlog:
        # if dest changelog is empty, get only first entry from source
        entry = False
        for line in src_chlog.splitlines():
            if line.startswith("*"):
                if entry:
                    break
                else:
                    entry = True
            relchlog.append(line)
    else:
        # Get relevant lines based on diff
        diff_txt = difflib.unified_diff(dst_chlog.splitlines(),
                                    src_chlog.splitlines())
        # Convert the diff text to a list of lines discarding the diff header
        diff_list = list(diff_txt)[3:]
        print diff_list
        # Logic to compare changelogs and extract relevant entries
        for line in diff_list:
            if line.startswith("+"):
                entry = line.replace("+", "", 1)
                relchlog.append(entry)
            elif line and line[0] in ("-", " "):
                # As soon as we hit a matching or removed line we skip out
                break

    # Now take the list of lines and create a list of changelog
    # entries by splitting on blanks
    ces = []
    ce = ""
    for line in relchlog:
        if _blankre.match(line):
            ces.append(ce)
            ce = ""
            continue # without adding the blank to the ce
        ce += line + "\n"
    # If we have any lines left they're a ce
    if ce:
        ces.append(ce)

    return ces

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

    def get_changes_file(self, prj, pkg, rev=None):
        """ Get a package's changes file """

        changelog = ""
        try:
            file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
            for fil in file_list:
                if fil.endswith(".changes"):
                    changelog = self.obs.getFile(prj, pkg, fil, revision=rev)
        except HTTPError, e:
            if e.code == 404:
                pass

        return changelog

    def get_relevant_changelogs(self, wid):
        """ Get relevant changelog entries for the actions of an OBS request
            and enrich each action's data structure with them """

        wid.result = False

        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        use_rev = False
        if wid.params.compare and wid.params.compare == "last_revision":
            use_rev = True

        for action in wid.fields.ev.actions:
            if action['type'] != "submit":
                continue
            if action.get("target", None):
                target_project = action["target"]["project"]
                target_package = action["target"]["package"]
                source_project = action["source"]["project"]
                source_package = action["source"]["package"]
                source_revision = action["source"]["rev"]
            else:
                target_project = action["targetproject"]
                target_package = action["targetpackage"]
                source_project = action["sourceproject"]
                source_package = action["sourcepackage"]
                source_revision = action["sourcerevision"]

            src_chlog = ""
            if use_rev:
                # get commit history
                commit_log = self.obs.getCommitLog(target_project,
                                                   target_package)
                # use the second last commit revision if available
                if len(commit_log) > 1 :
                    src_chlog = self.get_changes_file(target_project,
                                                      target_package,
                                                      str(commit_log[1][0]))
            else:
                src_chlog = self.get_changes_file(source_project,
                                                  source_package,
                                                  source_revision)

            dst_chlog = self.get_changes_file(target_project,
                                              target_package)

            rel_chlog = get_relevant_changelog(src_chlog, dst_chlog)
            print rel_chlog

            if rel_chlog:
                action["relevant_changelog"] = rel_chlog

        wid.result = True

    def handle_wi(self, wid):
        """ actual job thread """

        self.setup_obs(wid.fields.ev.namespace)
        self.get_relevant_changelogs(wid)
