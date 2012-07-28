#!/usr/bin/python

import socket

class ParticipantHandler(object):
    def notify(self, msg=["No 'message' for notify_irc"], channel="#meego-boss", highlight=""):
        # It depends on a reachable supybot instance with the Notify plugin
        ircbot = socket.socket()
        ircbot.connect((self.ircbot_host, self.ircbot_port))
        for m in msg:
            ircbot.send("%s %s%s\n" % (channel, highlight, m))
        ircbot.close()

    def handle_wi_control(self, ctrl):
        pass
    
    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.ircbot_host = "ircbot"
            self.ircbot_port = 5050
            if ctrl.config.has_section("notify_irc"):
                self.ircbot_host = ctrl.config.get("notify_irc", "ircbot_host", 0,
                                                   {"ircbot_host" : "ircbot"})
                self.ircbot_port = ctrl.config.getint("notify_irc", "ircbot_port", 0,
                                                   {"ircbot_port" : 5050})

    def handle_wi(self, wi):
        highlight = ""
        if wi.params.msg:
            msg = [wi.params.msg]
        elif wi.fields.msg:
            msg = wi.fields.msg
            if wi.fields.irc and wi.fields.irc.highlight:
                highlight = wi.fields.irc.highlight
        if msg:
            self.notify(msg=msg, channel=wi.params.irc_channel, highlight=highlight)
