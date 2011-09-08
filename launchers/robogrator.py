#!/usr/bin/python

from RuoteAMQP.launcher import Launcher

import os, socket

try:
    import json
except ImportError:
    import simplejson as json


class ParticipantHandler(object):

    def notify(self, msg):
        # This irc notifier will go.
        # It depends on a reachable supybot instance with the Notify plugin
        # TODO: the idea of the hardcoded IRC mechanism for notifications
        #       doesn't seem to be flexible. This method should be refactored
        #       not to rely on the presence of ircbot around (use python
        #       logging instead)
        #       See https://projects.maemo.org/bugzilla/show_bug.cgi?id=277361
        if self.irc_bothost:
            ircbot = socket.socket()
            ircbot.connect((self.irc_bothost, self.irc_botport))
            ircbot.send("%s %s" % (self.irc_channel, msg))
            ircbot.close
        print msg

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.process_store = ctrl.config.get("DEFAULT","process_store")
            self.irc_bothost = ctrl.config.get("irc","bothost") if (
                ctrl.config.has_option("irc","bothost")) else None
            self.irc_botport = ctrl.config.getint("irc","botport") if (
                ctrl.config.has_option("irc","botport")) else "5050"
            self.irc_channel = ctrl.config.get("irc","channel") if (
                ctrl.config.has_option("irc","channel")) else "#boss"
            amqp_host = ctrl.config.get("boss","amqp_host")
            amqp_user = ctrl.config.get("boss","amqp_user")
            amqp_pwd = ctrl.config.get("boss","amqp_pwd")
            amqp_vhost = ctrl.config.get("boss","amqp_vhost")
            self.launcher = Launcher(amqp_host=amqp_host,  amqp_user=amqp_user,
                                     amqp_pass=amqp_pwd, amqp_vhost=amqp_vhost)

    def handle_wi(self, wi):
        #print json.dumps(wi.to_h(), sort_keys=True, indent=4)

        ev = wi.fields.obsEvent
        if not ev:
            print "No Event"
            return

        if ev.format > 1 :
            obs = ev.namespace
            label = ev.label
        else:
            self.notify("Deprecated version 1 event received")
            (obs, label) = ev.type.split("_", 1)

         # identify project
        prj_name = None
        if ev.project:
            prj_name = ev.project
            self.notify("Got event %s from %s" % (label, prj_name))
            # Standard launch for most events
            self.launch(label, project = prj_name, ev = ev.as_dict())
            return

        # Most events are passed through to the relevant project; this
        # one is different as it may launch multiple processes.

        # A 'request' or group of actions (potentially to multiple
        # projects, potentially repeated) Only launch 1 process per
        # project though. The standard
        if label.startswith("SRCSRV_REQUEST"):
            targetprojects = []
            for action in ev.actions:
                targetproject = action['targetproject']
                if targetproject not in targetprojects:
                    targetprojects.append(targetproject)
                    self.notify("Got event %s for %s" % (label, prj_name))
                    # Detailed workitem.fields will be filled in by
                    # the standard_workflow_handler
                    self.launch(label, project=targetproject,
                                ev=ev.as_dict())
            return

        # Only fall through if EVENTS ARE NOT HANDLED
        self.notify("No project or actions in this %s event" % label)
        print wi.dump()

        return

    def getProcess(self, trigger, project):
        #FIXME: discuss structure
        try:
            p = project.replace(':', '/')
            process = open(os.path.join(self.process_store, p, trigger)).read()
            return process
        except:
            print "No process found for project %s trigger %s" % (project,
                                                                  trigger)
            return None

    def launch(self, name, **kwargs):
        # Specify a process definition
        if 'project' in kwargs:
            project = kwargs['project']
            self.notify("Looking to handle %s in %s" % (name, project))
            process = self.getProcess(name, project)
        if process:
            self.notify("Launching %s in %s" % (name, project))
            print process
            print json.dumps(kwargs, indent=4)
            self.launcher.launch(process, kwargs)

