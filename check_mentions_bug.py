#!/usr/bin/python

import re

# Check a bug/feature is mentioned in the changelog

class ParticipantHandler(object):

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
            self.bzs[bz]['method'] = config.get(bz, 'method')
            self.bzs[bz]['rest_slug'] = config.get(bz, 'rest_slug', None)
            self.bzs[bz]['bugzilla_server'] = config.get(bz, 'bugzilla_server')
            self.bzs[bz]['bugzilla_user'] = config.get(bz, 'bugzilla_user')
            self.bzs[bz]['bugzilla_pwd'] = config.get(bz, 'bugzilla_pwd')
            try:
                self.bzs[bz]['template'] = open(config.get(bz, 'comment_template')).read()
            except:
                raise Exception("Couldn't open " + config.get(bz, 'comment_template'))


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
        # Product is currently only useful if checking is asked for
        product = None

        for action in actions:
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
                        wi.result = True
                        return

        f.msg.append("""No bugs mentioned in relevant
                        changelog of package %s, please
                        refer to a bug using: %s""" %
                     (package, bugzilla['regexp']))

        return
