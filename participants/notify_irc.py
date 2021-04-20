#!/usr/bin/python

import socket


class ParticipantHandler(object):
    def notify(self, msg=["No 'message' for notify_irc"], channel="#meego-boss", highlight=""):
        ircbot = socket.socket()
        ircbot.connect((self.ircbot_host, self.ircbot_port))
        for item in msg:
            # Some bots handle multi-line messages,
            # the old supybot Notify plugin doesn't
            if self.split_lines:
                mls = item.splitlines()
            else:
                mls = [item]
            for m in mls:
                m = m.strip()
                if highlight and highlight[-1] != ' ':
                    highlight += ' '
                try:
                    line = u"%s %s%s\n" % (channel, highlight, m)
                    ircbot.send(line.encode('utf-8'))
                except:
                    self.log.exception("Failed to send message '%s'" % m)
                    ircbot.send(
                        "%s %s unable to send line, please check logs\n" %
                        (channel, highlight)
                    )
        ircbot.close()

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.ircbot_host = "ircbot"
            self.ircbot_port = 5050
            self.split_lines = True
            if ctrl.config.has_section("notify_irc"):
                self.ircbot_host = ctrl.config.get(
                    "notify_irc", "ircbot_host")
                self.ircbot_port = ctrl.config.getint(
                    "notify_irc", "ircbot_port")
                if ctrl.config.has_option("notify_irc", "split_lines"):
                    self.split_lines = ctrl.config.getboolean(
                        "notify_irc", "split_lines")

    def handle_wi(self, wi):
        highlight = ""
        msg = None
        if wi.params.msg:
            msg = [wi.params.msg]
        elif wi.fields.msg:
            msg = wi.fields.msg
            if wi.fields.irc and wi.fields.irc.highlight:
                highlight = wi.fields.irc.highlight
        if msg:
            self.notify(msg=msg, channel=wi.params.irc_channel, highlight=highlight)
