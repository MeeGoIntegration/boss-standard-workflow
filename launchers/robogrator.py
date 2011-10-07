#!/usr/bin/python

from RuoteAMQP.launcher import Launcher

import os, socket
from glob import iglob
import json


class ParticipantHandler(object):

    def __init__(self):

        self.process_store = None
        self.irc_botport = None
        self.irc_bothost = None
        self.launcher = None
        self.irc_channel = None

    def notify(self, msg):
        """ This irc notifier will go.
         It depends on a reachable supybot instance with the Notify plugin
         #TODO: the idea of the hardcoded IRC mechanism for notifications
               doesn't seem to be flexible. This method should be refactored
               not to rely on the presence of ircbot around (use python
               logging instead)
               See https://projects.maemo.org/bugzilla/show_bug.cgi?id=277361
        """
        if self.irc_bothost:
            ircbot = socket.socket()
            ircbot.connect((self.irc_bothost, self.irc_botport))
            ircbot.send("%s %s" % (self.irc_channel, msg))
            ircbot.close()
        print msg

    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.process_store = ctrl.config.get("robogrator","process_store")
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

    def get_process(self, trigger, project):
        """Returns a process and configuration file if available.

        This method returns a process file found from BOSS configurated 
        "process store", which is a file in a specific directory structure:

        <process_store>/<path>/<to/<project>/<trigger>.*.pdef

        eg.

        note : <process_store>/<path>/<to/<project>/<trigger> is deprecated
        and might be removed in future versions. Also config files will only be
        picked up if you have new style process names.

        /srv/BOSS/processes/FOO/Trunk/SRCSRV_REQUEST_CREATE.01-STABLE.pdef
        
        It also returns the corresponding configuration file if one is found
        in process_file_name.conf:

        <process_store>/<path>/<to/<project>/<trigger>.*.conf

        eg.

        /srv/BOSS/processes/FOO/Trunk/SRCSRV_REQUEST_CREATE.01-STABLE.conf

        The configuration is formatted as JSON and supports single line 
        comments:

        # A comment
        "key": "value"

        but NOT:
        "key": "value" # A comment

        :param trigger: The triggering event
        :param project: Project directory to use
        :returns: Generator that yields tuples consisting of process and config
        """

        process = None
        pbase = os.path.join(self.process_store, project.replace(':', '/'),
                             trigger)
        # OLD name for backward compat
        try:
            with open(pbase, 'r') as pdef_file:
                process = pdef_file.read()
            self.notify("Found old style pdef %s" % pbase)
            print "*"*80
            print "DEPRECATED: please rename process at \n%s" % pbase
            print "*"*80
            yield None, process
        except IOError as (errorno, errorstr):
            # if there is no file found or there are any weird errors due 
            # to race conditions like the file is removed before or while
            # reading it, skip the exception
            pass

        # iglob returns an iterator which will do the right thing when empty
        for filename in iglob("%s.*.pdef" % pbase):
            try:
                with open(filename, 'r') as pdef_file:
                    process = pdef_file.read()
                self.notify("Found pdef %s" % filename)
            except IOError as (errorno, errorstr):
                # Any weird errors due to race conditions are ignored
                # for example the file is removed before or while reading it
                print "I/O error({0}): {1}".format(errorno, errorstr)
                continue

            try:
                config = None
                with open("%s.conf" % filename[:-5], 'r') as config_file:
                    lines = config_file.readlines()
                    for line in lines:
                        if not line.strip() or line.strip().startswith('#'):
                            lines.remove(line)
                    config = "\n".join(lines).strip()
                    config = json.loads(config)
                self.notify("Found valid conf %s.conf" % filename[:-5])
            except IOError as (errorno, errorstr):
                # we don't care if there is no .conf file
                # so we ignore errorcode 2 which is file not found
                # otherwise print the error and don't launch the process
                if not errorno == 2:
                    print "I/O error({0}): {1}".format(errorno, errorstr)
                    continue
            except ValueError, error:
                # if a .conf was found but is invalid don't launch the process
                print "invalid conf file %s.conf\n%s" % (filename, error)
                continue

            yield config, process

    def launch(self, name, **kwargs):
        # Specify a process definition
        if 'project' in kwargs:
            project = kwargs['project']
            self.notify("Looking to handle %s in %s" % (name, project))
            for config, process in self.get_process(name, project):
                if config:
                    for key, value in config.iteritems():
                        kwargs[key] = value
                self.notify("Launching %s in %s" % (name, project))
                self.launcher.launch(process, kwargs)

