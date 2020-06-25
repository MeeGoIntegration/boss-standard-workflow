import xmlrpc.client, urllib.request, urllib.parse, urllib.error

from io import StringIO

from boss.bz.base import BaseBugzilla, BugzillaError


class BugzillaXMLRPC(BaseBugzilla):
    """XMLRPC API Client implementation."""

    def __init__(self, bz_conf):
        super(BugzillaXMLRPC, self).__init__()

        # Needed by both basic auth and by the API login
        self._user = bz_conf['user']
        self._passwd = bz_conf['password']
        url_s = list(urllib.parse.urlsplit(bz_conf['server']))

        if bz_conf['use_http_auth']:
            url_s[1] = f'{self._user}:{self._passwd}@{url_s[1]}'
        self._server = urllib.parse.urlunsplit(url_s)

        self._rpc = xmlrpc.client.ServerProxy(self._server)

    def __xmlrpc_call(self, name, param):
        """Helper to make the xml-rpc call and handle faults."""
        try:
            method = getattr(self._rpc, name)
            return method(param)
        except xmlrpc.client.Fault as fault:
            code = getattr(fault, "faultCode", None)
            if code is None:
                msg = str(fault)
            else:
                msg = getattr(fault, "faultString", str(fault))
            raise BugzillaError(code, msg)

    def login(self):
        self.__xmlrpc_call("User.login", {
                "login": self._user,
                "password": self._passwd,
                "remember": True})

    def bug_get(self, bug_id):
        result = self.__xmlrpc_call("Bug.get", {"ids": [bug_id]})
        if result.get("bugs"):
            return result["bugs"][0]
        else:
            raise BugzillaError(None, "Failed to get bug %s" % bug_id)

    def comments_get(self, bug_id):
        result = self.__xmlrpc_call("Bug.comments", {"ids": [bug_id]})
        if result.get("bugs"):
            return result["bugs"][bug_id]
        else:
            raise BugzillaError(None, "Failed to get bug %s" % bug_id)

    def comment_get(self, bug_id, comment_id):
        result = self.__xmlrpc_call("Bug.comments", {"ids": [bug_id]})
        if result.get("bugs"):
            bug = result["bugs"][bug_id]
            for comment in bug['comments']:
                if comment['count'] == comment_id:
                    return comment
        else:
            raise BugzillaError(None, "Failed to get bug %s" % bug_id)

    def bug_update(self, bug_data):
        bug_id = bug_data.get("id")
        if bug_id is None:
            raise BugzillaError(None, "Bug ID needed for update")
        params = {"ids": [bug_id]}
        for key in bug_data:
            if key in ("id",):
                continue
            params[key] = bug_data[key]
        self.__xmlrpc_call("Bug.update", params)

    def comment_add(self, bug_id, comment, is_private):
        self.__xmlrpc_call("Bug.add_comment",
                           {"id": bug_id, "comment": comment,
                            "is_private": is_private})

    def tracking_bugs(self, remotes):
        """This is a non-standard RPC that comes from RemoteTrack extension
        https://github.com/bayoteers/RemoteTrack
        """
        return self.__xmlrpc_call(
            "RemoteTrack.tracking_bugs",
            {"remotes": remotes, "create": True}
        )


class MockFile(StringIO):

    def getheader(self, header_name, default):
        return default
