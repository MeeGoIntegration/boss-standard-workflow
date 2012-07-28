#!/usr/bin/python

from RuoteAMQP import Launcher
import json
import sys
import ConfigParser, os

workitem = None
pconf = {} 

if len(sys.argv) == 1 or len(sys.argv) > 3:
    print "usage: launcher.py <process.pdef> [workitem.json]"
    sys.exit(1)
elif len(sys.argv) == 3:
    workitem = sys.argv[2]

pdef = sys.argv[1]
process = open(pdef).read()

try:
    with open("%s.conf" % pdef[:-5], 'r') as config_file:
        lines = [line.strip() if not line.strip().startswith('#') \
                 else "" for line in config_file.readlines()]
        pconf = json.loads("\n".join(lines))
    print "Found valid conf %s.conf" % pdef[:-5]
except IOError as exc:
    # we don't care if there is no .conf file
    # so we ignore errorcode 2 which is file not found
    # otherwise print the error and don't launch the process
    if not exc.errno == 2:
        raise

if workitem:
    wid = open(workitem).read()
    pconf.update(json.loads(wid))

config = ConfigParser.ConfigParser(
                  {"amqp_host" : "127.0.0.1:5672",
                  "amqp_user" : "boss",
                  "amqp_pwd" : "boss",
                  "amqp_vhost" : "boss"
                  })

if os.path.exists("/etc/skynet/skynet.conf"):
    config.readfp(open('/etc/skynet/skynet.conf'))

launcher = Launcher(amqp_host = config.get("boss", "amqp_host"),
                    amqp_user = config.get("boss", "amqp_user"),
                    amqp_pass = config.get("boss", "amqp_pwd"),
                    amqp_vhost = config.get("boss", "amqp_vhost"))

launcher.launch(process, pconf)

