#!/usr/bin/python

# The message containers are a minimal requirement
from SkyNET import (WorkItemCtrl, ParticipantCtrl, Workitem)
import socket

class ParticipantHandler(object):
    def notify(self, msg="No 'message' for notify_irc", channel="#meego-boss"):
        # This irc notifier will go.
        # It depends on a reachable supybot instance with the Notify plugin
        ircbot = socket.socket()
        ircbot.connect(("ircbot",5050))
        ircbot.send("%s %s" % (channel, msg))
        ircbot.close()
        print channel, msg

    def handle_wi_control(self, ctrl):
        pass
    
    def handle_lifecycle_control(self, ctrl):
        pass
    
    def handle_wi(self, wi):
        if wi.params.msg:
            msg = wi.params.msg
        elif wi.fields.msg:
            msg = "\n".join(wi.fields.msg)
        else:
            return

        self.notify(msg, wi.params.irc_channel)
