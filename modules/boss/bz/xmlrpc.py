import xmlrpclib, pycurl, urllib

from StringIO import StringIO

from boss.bz.base import BaseBugzilla, BugzillaError


class BugzillaXMLRPC(BaseBugzilla):
    """XMLRPC API Client implementation."""

    def __init__(self, bz_conf):
        super(BugzillaXMLRPC, self).__init__()

        self._server = bz_conf['server']
        self._user = bz_conf['user']
        self._passwd = bz_conf['password']
        transport_params = {
            'proto':  urllib.splittype(self._server)[0]
        }
        if bz_conf['use_http_auth']:
            transport_params['username'] = self._user
            transport_params['password'] = self._passwd

        self._rpc = xmlrpclib.ServerProxy(self._server,
                transport=PyCURLTransport(**transport_params))

    def __xmlrpc_call(self, name, param):
        """Helper to make the xml-rpc call and handle faults."""
        try:
            method = getattr(self._rpc, name)
            return method(param)
        except xmlrpclib.Fault as fault:
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
                {"id": bug_id, "comment": comment, "is_private": is_private})

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

class PyCURLTransport(xmlrpclib.Transport):
    """Handles a cURL HTTP transaction to an XML-RPC server."""

    def __init__(self, username=None, password=None, timeout=0, proto="http",
            use_datetime=False):
        """
        Constructor. Has to invoke parent constructor with 'use_datetime'
        argument.
        """
        xmlrpclib.Transport.__init__(self, use_datetime)

        self.verbose = 0
        self._proto = proto

        self._curl = pycurl.Curl()

        # Suppress signals
        self._curl.setopt(pycurl.NOSIGNAL, 1)

        # Follow redirects
        self._curl.setopt(pycurl.FOLLOWLOCATION, 1)

        # Store cookies for this handle
        self._curl.setopt(pycurl.COOKIEFILE, "")

        # Set timeouts
        if timeout:
            self._curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
            self._curl.setopt(pycurl.TIMEOUT, timeout)

        # XML-RPC calls are POST (text/xml)
        self._curl.setopt(pycurl.POST, 1)
        self._curl.setopt(pycurl.HTTPHEADER, ["Content-Type: text/xml"])

        # Set auth info if defined
        if username and password:
            self._curl.setopt(pycurl.USERPWD, "%s:%s" % (username, password))

    def _check_return(self, host, handler, httpcode, buf):
        """Check for errors."""
        pass

    def request(self, host, handler, request_body, verbose = 0):
        """Performs actual request."""
        buf = MockFile()
        self._curl.setopt(pycurl.URL,
                str("%s://%s%s" % (self._proto, host, handler)))
        self._curl.setopt(pycurl.POSTFIELDS, request_body)
        self._curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        self._curl.setopt(pycurl.VERBOSE, verbose)
        self.verbose = verbose
        try:
            self._curl.perform()
            httpcode = self._curl.getinfo(pycurl.HTTP_CODE)
        except pycurl.error, err:
            raise xmlrpclib.ProtocolError(
                    host + handler,
                    err[0],
                    err[1],
                    None)

        self._check_return(host, handler, httpcode, buf)

        if httpcode != 200:
            raise xmlrpclib.ProtocolError(
                    host + handler,
                    httpcode,
                    buf.getvalue(),
                    None)

        buf.seek(0)
        return self.parse_response(buf)


