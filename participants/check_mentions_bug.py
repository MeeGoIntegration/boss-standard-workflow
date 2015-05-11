#!/usr/bin/python
"""
Allows to check that new changelog entries refer to a bug or feature number

The comment can be populated using a string or a template.

.. warning ::

   * The get_relevant_changelog participant should have been run first to fetch
     the relevant changelog entries

   * The check_has_relevant_changelog paritipant should have been run first to
     make sure all packages in the promotion request have relevant changelog
     entries

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.

:term:`Workitem` fields OUT :

:Returns:
   result(boolean):
      True if all changelog entries mentioned a bug number, FALSE otherwise.

"""

import re
from boss.bz.config import parse_bz_config

class ParticipantHandler(object):

    """ Class implementation as required by the API"""

    def __init__(self):
        self.bzs = None

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.setup_config(ctrl.config)

    def setup_config(self, config):
        self.bzs = parse_bz_config(config)

    def handle_wi(self, wi):
        """ actual job thread """
        wi.result = False
        f = wi.fields

        if not f.msg: f.msg = []
        # Support both ev.actions and plain workitem
        actions = f.ev.actions
        if not actions:
            package = f.package
            relchloge = f.relevant_changelog
            if not relchloge or not package:
                raise RuntimeError("Fields 'relevant_changelog' and 'package' "
                        "are mandatory when handling a request")
            # Pack the flat workitem data bits into a fake actions array
            # so we can reuse the same code path
            actions = [{ "targetpackage" : package,
                         "relevant_changelog" : relchloge }]


        # Platform is used if it is present. NOT mandatory
        platform = f.platform
        result = True

        for action in actions:
            bugs = []
            if not action["type"] == "submit":
                continue
            if "targetpackage" not in action:
                f.msg.append("Missing targetpackage in the SR")
                result = False
                continue

            if f.exclude_prjs:
                skip=False
                for exc in f.exclude_prjs:
                  if action["targetproject"] in re.compile(exc).findall(action["targetproject"]):
                      skip=True
                if skip:
                    continue

            package = action["targetpackage"]

            if "relevant_changelog" not in action:
                continue
            relchloge = action["relevant_changelog"]

            # Go through each bugzilla we support
            for (bugzillaname, bugzilla) in self.bzs.iteritems():
                # if this tracker is used for this platform
                if platform and platform not in bugzilla['platforms']:
                    continue

                # And then for each changelog deal with each bug
                # mentioned
                for chloge in relchloge:
                    for m in bugzilla['compiled_re'].finditer(chloge):
                        bugnum = m.group('key')
                        bugs.append(bugnum)
                    for remote_re in bugzilla['remote_tags_re']:
                        for match in remote_re.finditer(chloge):
                            bugs.append(match.group())
            if not bugs:
                result = False
                f.msg.append("No bugs mentioned in relevant changelog of "\
                             "package %s, please refer to a bug using: "\
                             "%s" % (package,
                                     bugzilla['regexp']))
        wi.result = result

