#!/usr/bin/python
""" Quality check participant """

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass
    
    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        msg = wid.fields.msg if wid.fields.msg else []
        actions = wid.fields.ev.actions

        if not actions:
            wid.set_field("__error__", "A needed field does not exist.")
            return

        result = True

        # Assert each package being submitted has relevant changelog entries.
        for action in actions:
            if not "relevant_changelog" in action:
                result = False
                msg.append("Package %s from project %s does not contain new \
                            changelog entries compared to package %s in \
                            project %s" % (action['sourcepackage'],
                                           action['sourceproject'],
                                           action['targetpackage'],
                                           action['targetproject']))

        wid.set_field("msg", msg)
        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump() 

        self.quality_check(wid)
