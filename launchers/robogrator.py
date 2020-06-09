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

        TODO:
            The idea of the hardcoded IRC mechanism for notifications
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
        self.log.info(msg)

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
        self.log.debug(json.dumps(wi.to_h(), sort_keys=True, indent=4))

        ev = wi.fields.obsEvent
        if not ev:
            self.log.info("No Event")
            return

        if ev.format > 1 :
            obs = ev.namespace
            label = ev.label
        else:
            self.notify("Deprecated version 1 event received")
            (obs, label) = ev.type.split("_", 1)

         # identify project
        if ev.project:
            # Standard launch for most events
            self.launch(label, project=ev.project, ev=ev.as_dict())
            return

        # Most events are passed through to the relevant project; this
        # one is different as it may launch multiple processes.

        # A 'request' or group of actions (potentially to multiple
        # projects, potentially repeated) Only launch 1 process per
        # project though. The standard
        if label.startswith("SRCSRV_REQUEST"):
            targetprojects = []
            for action in ev.actions:
                targetproject = action['targetproject'] \
                             or action['deleteproject']
                if targetproject not in targetprojects:
                    targetprojects.append(targetproject)
                    self.launch(label, project=targetproject,
                                ev=ev.as_dict())
            return

        # Only fall through if EVENTS ARE NOT HANDLED
        self.notify("No project or actions in this %s event" % label)
        self.log.info(wi.dump())

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
            self.log.warning("Found old style pdef %s" % pbase)
            self.log.warning("*"*80)
            self.log.warning("DEPRECATED: please rename process at \n%s" % pbase)
            self.log.warning("*"*80)
            yield None, process
        except IOError:
            # if there is no file found or there are any weird errors due 
            # to race conditions like the file is removed before or while
            # reading it, skip the exception
            pass

        # iglob returns an iterator which will do the right thing when empty
        for filename in iglob("%s.*.pdef" % pbase):
            try:
                with open(filename, 'r') as pdef_file:
                    process = pdef_file.read()
                self.log.info("Found pdef %s" % filename)
            except IOError as exc:
                # Any weird errors due to race conditions are ignored
                # for example the file is removed before or while reading it
                self.log.info("I/O error({0}): {1} {2}".format(exc.errno, exc.strerror,
                                                       exc.filename))
                continue

            try:
                config = None
                with open("%s.conf" % filename[:-5], 'r') as config_file:
                    lines = [line.strip() if not line.strip().startswith('#') \
                             else "" for line in config_file.readlines()]
                    config = json.loads("\n".join(lines))
                self.log.info("Found valid conf %s.conf" % filename[:-5])
            except IOError as exc:
                # we don't care if there is no .conf file
                # so we ignore errorcode 2 which is file not found
                # otherwise self.log.info(the error and don't launch the process)
                if not exc.errno == 2:
                    err = "I/O error({0}): {1} {2}".format(exc.errno,
                                                           exc.strerror,
                                                           exc.filename)
                    self.log.error(err)
                    raise RuntimeError(err)
            except ValueError as error:
                # if a .conf was found but is invalid don't launch the process
                err = "invalid conf file %s.conf\n%s" % (filename, error)
                self.notify(err)
                raise RuntimeError(err)

            yield config, process

    def launch(self, name, **kwargs):
        # Specify a process definition
        if 'project' in kwargs:
            project = kwargs['project']
            self.notify("Looking to handle %s in %s" % (name, project))
            for config, process in self.get_process(name, project):
                if config:
                    for key, value in config.items():
                        kwargs[key] = value
                self.notify("Launching %s in %s" % (name, project))
                self.launcher.launch(process, kwargs)

