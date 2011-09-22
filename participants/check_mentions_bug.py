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

class ParticipantHandler(object):

    """ Class implementation as required by the API"""

    def __init__(self):
        self.bzs = None

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.setup_config(ctrl.config)

    def setup_config(self, config):
        supported_bzs = config.get("bugzilla", "bzs").split(",")
        self.bzs = {}
    # FIXME: should use revs api
        for bz in supported_bzs:
            self.bzs[bz] = {}
            self.bzs[bz]['platforms'] = config.get(bz, 'platforms').split(',')
            self.bzs[bz]['regexp'] = config.get(bz, 'regexp')
            self.bzs[bz]['compiled_re'] = re.compile(config.get(bz, 'regexp'))

    def handle_wi(self, wi):

        wi.result = False
        f = wi.fields

        if wi.params.debug_dump or f.debug_dump:
            print wi.dump()

        if not f.msg: f.msg = []
        # Support both ev.actions and plain workitem
        actions = f.ev.actions
        if not actions:
            package = f.package
            relchloge = f.relevant_changelog
            if not relchloge or not package:
                f.__error__ = "Need relevant_changelog and \
                             package when not handling a request."
                f.msg.append(f.__error__)
                raise RuntimeError("Missing mandatory field")
            # Pack the flat workitem data bits into a fake actions array
            # so we can reuse the same code path
            actions = [{ "targetpackage" : package,
                         "relevant_changelog" : relchloge }]


        # Platform is used if it is present. NOT mandatory
        platform = f.platform
        result = True

        for action in actions:
            bugs = []
            package = action["targetpackage"]
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
                        bugs.append(bugnum)
            if not bugs:
                result = False
                f.msg.append("No bugs mentioned in relevant changelog of "\
                             "package %s, please refer to a bug using: "\
                             "%s" % (package,
                                     bugzilla['regexp']))
        wi.result = result

