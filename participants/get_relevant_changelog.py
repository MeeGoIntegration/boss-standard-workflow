#!/usr/bin/python
""" This participants gets the relevant changelog entries of the packages being
submitted by comparing its changes file to the one in the destination,
OR by comparing the destination changes file to its previous revision.
It then extends the actions array with these results.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

   new_changelog_count(integer):
      Optional. Number of new entries to process in case destination package
      doesn't exist.

:term:`Workitem` params IN

:Parameters:
   compare(string):
      if "last_revision" the relevant changelog entries will be obtained by
      comparing to the previous revision of the file in the destination.
      Otherwise it compares the changes file from source to the destination.

   project(string):
      Project name to get package from.
      If specified then ev.actions is not needed

   package(string):
      Package name to get changelog from.
      If specified then ev.actions is not needed

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      False if getting relevant changelog failed, True otherwise

   ev.actions.relevant_changelog(list):
      Extends the submit request data structure :term:`actions` with the
      relevant_changelog field which contains a list of changelog entries

"""


import re
from urllib2 import HTTPError

from boss.obs import BuildServiceParticipant

_blankre = re.compile(r"^\s*$")


def _diff_chlog(oldlogs, newlogs):

    chlog = []
    skip = False
    for line in newlogs:
        if line.startswith("*"):
            if line not in oldlogs:
                chlog.append(line)
                skip = False
            else:
                skip = True
                continue
        else:
            if not skip:
                chlog.append(line)

    return chlog


def get_relevant_changelog(src_chlog, dst_chlog, new_count=None):
    """ Diff two changelogs and return the list of lines that are only in
        the source changelog """

    relchlog = []
    # compare source changelog to dest changelog
    if not src_chlog:
        # If source is empty, do nothing
        pass
    elif not dst_chlog:
        # if dest changelog is empty, get all or new_count entries from source
        count = 0
        for line in src_chlog.splitlines():
            if line.startswith("*"):
                if new_count:
                    if count == new_count:
                        break
                    else:
                        count += 1
            relchlog.append(line)
    else:
        relchlog = _diff_chlog(dst_chlog.splitlines(), src_chlog.splitlines())

    # Now take the list of lines and create a list of changelog
    # entries by splitting on blanks
    ces = []
    ce = ""
    for line in relchlog:
        if _blankre.match(line):
            ces.append(ce)
            ce = ""
            continue  # without adding the blank to the ce
        ce += line + "\n"
    # If we have any lines left they're a ce
    if ce:
        ces.append(ce)

    return ces


class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

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

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread

        Get relevant changelog entries for the actions of an OBS request
        and enrich each action's data structure with them """

        wid.result = False

        if not wid.fields.ev.actions:
            if wid.params.project and wid.params.package:
                action = {
                    'type': 'submit',
                    'targetproject': wid.params.project,
                    'targetpackage': wid.params.package,
                    'sourceproject': wid.params.project,
                    'sourcepackage': wid.params.package,
                    'sourcerevision': "latest"
                }

                wid.fields.ev.actions = [action]
            else:
                raise RuntimeError("Missing mandatory field 'ev.actions'")

        actions = wid.fields.ev.actions

        use_rev = False
        if wid.params.compare and wid.params.compare == "last_revision":
            use_rev = True

        new_count = wid.fields.new_changelog_count
        if new_count:
            try:
                new_count = int(new_count)
            except ValueError:
                raise RuntimeError(
                    "Wrong optional field new_changelog_count, "
                    "should be an integer"
                )

        for action in actions:
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
                commit_log = self.obs.getCommitLog(
                    target_project, target_package
                )

                rev = None
                # use the second last commit revision if available
                if len(commit_log) > 1:
                    rev = str(commit_log[1][0])

                dst_chlog = self.get_changes_file(
                    target_project, target_package, rev)

                src_chlog = self.get_changes_file(
                    target_project, target_package)

            else:
                src_chlog = self.get_changes_file(
                    source_project, source_package, source_revision)

                dst_chlog = self.get_changes_file(
                    target_project, target_package)

            rel_chlog = get_relevant_changelog(src_chlog, dst_chlog, new_count)
            print rel_chlog

            if rel_chlog:
                action["relevant_changelog"] = [
                    entry.decode('UTF-8', 'replace') for entry in rel_chlog
                ]

        wid.result = True
