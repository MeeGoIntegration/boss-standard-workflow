import os
import re
from boss.bz.xmlrpc import BugzillaXMLRPC
from boss.bz.rest import BugzillaREST

def parse_bz_config(config):

    bzs={}
    supported_bzs = config.get("bugzilla", "bzs").split(",")
    for bz in supported_bzs:
        bzs[bz] = {}
        bzs[bz]['name'] = bz
        bzs[bz]['platforms'] = config.get(bz, 'platforms').split(',')
        bzs[bz]['regexp'] = config.get(bz, 'regexp')
        bzs[bz]['compiled_re'] = re.compile(config.get(bz, 'regexp'), flags=re.IGNORECASE)
        bzs[bz]['method'] = config.get(bz, 'method')
        if bzs[bz]['method'] == 'REST':
            bzs[bz]['rest_slug'] = config.get(bz, 'rest_slug')
        bzs[bz]['server'] = config.get(bz, 'bugzilla_server')
        bzs[bz]['user'] = config.get(bz, 'bugzilla_user')
        bzs[bz]['password'] = config.get(bz, 'bugzilla_pwd')

        bzs[bz]['use_http_auth'] = False
        if config.has_option(bz, "use_http_auth"):
            bzs[bz]['use_http_auth'] = config.getboolean(bz, "use_http_auth")

        template = config.get(bz, 'comment_template')
        try:
            bzs[bz]['template'] = open(template).read()
        except:
            raise RuntimeError("Couldn't open %s" % template)
        if config.has_option(bz, "template_store"):
            bzs[bz]['template_store'] = config.get(bz, 'template_store')
        else:
            # backwards compatibility for old config files
            bzs[bz]['template_store'] = os.path.dirname(template)

        method = bzs[bz]['method']
        if method == 'REST':
            bzs[bz]['interface'] = BugzillaREST(bzs[bz])
        elif method == 'XMLRPC':
            bzs[bz]['interface'] = BugzillaXMLRPC(bzs[bz])
        else:
            raise RuntimeError("Bugzilla method %s not implemented"
                               % method)

        if config.has_option(bz, "remote_tags"):
            bzs[bz]['remote_tags'] = config.get(bz, "remote_tags").split(',')
            bzs[bz]['remote_tags_re'] = [re.compile(tag) for tag in bzs[bz]['remote_tags']]
        else:
            bzs[bz]['remote_tags'] = []
            bzs[bz]['remote_tags_re'] = []

    return bzs
