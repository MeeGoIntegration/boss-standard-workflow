#!/usr/bin/python

import json
import logging
import os
import socket
from collections import defaultdict
from glob import iglob

try:
    from RuoteAMQP.launcher import Launcher
except:
    if __name__ != '__main__':
        raise


class ParticipantHandler(object):

    def __init__(self):

        self.store = None
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
            self.store = ProcessStore(
                store=ctrl.config.get("robogrator", "process_store"),
                log=self.log,
            )
            self.irc_bothost = ctrl.config.get("irc", "bothost") if (
                ctrl.config.has_option("irc", "bothost")) else None
            self.irc_botport = ctrl.config.getint("irc", "botport") if (
                ctrl.config.has_option("irc", "botport")) else "5050"
            self.irc_channel = ctrl.config.get("irc", "channel") if (
                ctrl.config.has_option("irc", "channel")) else "#boss"
            amqp_host = ctrl.config.get("boss", "amqp_host")
            amqp_user = ctrl.config.get("boss", "amqp_user")
            amqp_pwd = ctrl.config.get("boss", "amqp_pwd")
            amqp_vhost = ctrl.config.get("boss", "amqp_vhost")
            self.launcher = Launcher(amqp_host=amqp_host,  amqp_user=amqp_user,
                                     amqp_pass=amqp_pwd, amqp_vhost=amqp_vhost)

    def handle_wi(self, wi):
        self.log.debug(json.dumps(wi.to_h(), sort_keys=True, indent=4))

        ev = wi.fields.obsEvent
        if not ev:
            self.log.info("No Event")
            return

        if ev.format > 1:
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

    def launch(self, name, **kwargs):
        # Specify a process definition
        if 'project' in kwargs:
            project = kwargs['project']
            self.notify("Looking to handle %s in %s" % (name, project))
            for config, process in self.store.get_processes(name, project):
                if config:
                    for key, value in config.iteritems():
                        kwargs[key] = value
                self.notify("Launching %s in %s" % (name, project))
                self.launcher.launch(process, kwargs)


class ProcessStore(object):
    def __init__(self, store=None, log=None):
        self.log = log or logging.getLogger('ProcessStore')
        self.store_root = store or os.getcwd()

    def get_processes(self, trigger, project):
        """Get processes and configurations for given trigger and project

        :param trigger: The triggering event
        :param project: Project name to use in the base search path
        :returns: Generator that yields tuples consisting of process and config

        This method returns a process file found from BOSS configurated
        "process store", which is a file in a specific directory structure:

            <process_store>/<project_path>/<trigger>.<process_name>.pdef

        where
            project_path - OBS project name where : is replaced with /
            trigger      - OBS even name
            process_name - free form identifier of the process

        eg.

            /srv/BOSS/processes/mer/core/SRCSRV_REQUEST_CREATE.01-STABLE.pdef

        It also returns the corresponding configuration by looking for matching
        file in the same directory with extension .conf:

            <trigger>.<process name>.conf

        eg.

            /srv/BOSS/processes/FOO/Trunk/SRCSRV_REQUEST_CREATE.01-STABLE.conf


        The configuration file formatted is JSON, with supports for single line
        comments:

            {
                # A comment
                "key": "value"
            }

        but comments can NOT be included on other lines, like:

            {
                "key": "value" # A comment
            }


        If the project dir contains a symbolic link named '_parent', process
        definitions and config files are inherited from the linked directory.

        Inherited processes can be disabled by creating an empty file named:

            <trigger>.<process name>.disable

        Inherited process configuration files can be either overwiten, or
        extended by merging. The mergin is done by creating a conf with name:

            <trigger>.<process name>.merge_conf

        Merging happens as a deep merge so that parent conf like:

            {
                "image": {
                    "arch": "i486",
                    "name": "test",
                    "image_type": "fs"
                },
                "something": "else"
            }

        and merge_conf like:

            {
                "image": {
                    "arch": "armv7hl",
                    "new": "value"
                },
                "something": null
            }

        would result in:

            {
                "image": {
                    "arch": "armv7hl",
                    "name": "test",
                    "image_type": "fs",
                    "new": value"
                }
            }
        """

        process = None
        process_dirs = self._get_process_dirs(project)
        # Find process definition and config files
        pdefs = {}
        pconfs = defaultdict(list)
        for process_dir in process_dirs:
            pdef_glob = os.path.join(process_dir, trigger) + '.*'
            self.log.debug('Looking for files with %s' % pdef_glob)
            for file_path in iglob(pdef_glob):
                _, file_name = os.path.split(file_path)
                process_name, ext = os.path.splitext(file_name)
                if ext in ['.conf', '.merge_conf']:
                    self.log.debug('Conf file %s' % file_path)
                    pconfs[process_name].append(file_path)
                elif ext == '.disable' and process_name in pdefs:
                    self.log.debug('Disable pdef %s' % file_path)
                    del pdefs[process_name]
                elif ext == '.pdef':
                    self.log.debug('Pdef file %s' % file_path)
                    pdefs[process_name] = file_path
                else:
                    self.log.debug('Unknown ext %s: %s' % (ext, file_path))

        for process_name, pdef_file in pdefs.items():
            # Read process definition
            try:
                with open(pdef_file, 'r') as fd:
                    process = fd.read()
                self.log.info("Using pdef %s" % pdef_file)
            except IOError as exc:
                # Any weird errors due to race conditions are ignored
                # for example the file is removed before or while reading it
                self.log.error(
                    "I/O error(%s): %s %s" % (
                        exc.errno, exc.strerror, exc.filename)
                )
                continue
            # Read and merge configuration files
            config = None
            baseconf = None
            mergedconfs = []
            for conf_file in pconfs[process_name]:
                try:
                    with open(conf_file, 'r') as fd:
                        lines = [
                            line for line in fd.readlines()
                            if not line.strip().startswith('#')
                        ]
                        data = json.loads("\n".join(lines))
                    self.log.debug("Found valid conf %s" % conf_file)
                except IOError as exc:
                    self.log.error(
                        "I/O error(%s): %s %s" % (
                            exc.errno, exc.strerror, exc.filename)
                    )
                    break
                except ValueError as exc:
                    # if the conf is invalid don't launch the process
                    self.log.error(
                        "invalid conf file %s\n%s" % (conf_file, exc)
                    )
                    break
                _, ext = os.path.splitext(conf_file)
                if ext == '.merge_conf':
                    if config is None:
                        self.log.error(
                            '%s has no parent conf, cannot merge' % conf_file
                        )
                        break
                    mergedconfs.append(conf_file)
                    self._merge_config(config, data)
                else:
                    baseconf = conf_file
                    config = data
            else:
                # No break in for loop -> conf files parsed successfully
                if baseconf:
                    msg = 'Using base conf %s' % baseconf
                    if mergedconfs:
                        msg += ' extended with %s' % ', '.join(mergedconfs)
                    self.log.info(msg)
                yield config, process

    def _get_process_dirs(self, project):
        base_dir = os.path.join(self.store_root, *project.split(':'))
        self.log.debug('Checking project dir %s' % base_dir)
        dirs = []
        if not os.path.exists(base_dir):
            self.log.debug('Does not exist: %s' % base_dir)
            return dirs

        if os.path.islink(base_dir):
            self.log.warning('%s is a link' % base_dir)
            base_dir = os.path.realpath(base_dir)

        if os.path.isdir(base_dir):
            parent_link = os.path.join(base_dir, '_parent')
            if os.path.exists(parent_link):
                with open(parent_link) as fd:
                    parent_project = fd.readline().strip()
                if parent_project:
                    self.log.debug('Using parent project %s' % parent_project)
                    parents = self._get_process_dirs(parent_project)
                    if base_dir in parents:
                        self.log.error(
                            'Loop detected in project inheritance: %s <- %s' %
                            ' <- '.join(parents), base_dir,
                        )
                        return dirs
                    dirs.extend(parents)
            dirs.append(base_dir)
        else:
            self.log.warning('Not a directory %s' % base_dir)
        return dirs

    def _merge_config(self, config, merge):
        for key, value in merge.items():
            if isinstance(value, dict):
                tmp = config.get(key, {})
                self._merge_config(tmp, value)
                config[key] = tmp
            elif value is None:
                config.pop(key, None)
            else:
                config[key] = value


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Processs store debug utility"
    )
    parser.add_argument(
        '--store', '-s',
        default=os.getcwd(),
        help='Process store path',
    )
    parser.add_argument(
        '--trigger', '-t',
        required=True,
        help='Trigger event name',
    )
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name'
    )
    parser.add_argument(
        '--debug', '-d',
        default=False,
        action='store_true',
        help='Enable debug output',
    )
    args = parser.parse_args()
    log = logging.getLogger()
    log.addHandler(logging.StreamHandler())
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    store = ProcessStore(store=args.store, log=log)
    for config, process in store.get_processes(args.trigger, args.project):
        log.info("** Would launch")
        log.info(process)
        if config:
            log.info(json.dumps(config, indent=2))
        else:
            log.info('No config')
