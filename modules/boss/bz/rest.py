"""Rest API Bugzilla clien."""

import json, urllib.request, urllib.parse, urllib.error

from boss.bz.base import BaseBugzilla, BugzillaError



class BugzillaREST(BaseBugzilla):
    """Rest API client implementation."""

    def __init__(self, bz_conf):
        super(BugzillaREST, self).__init__()

        self._server = bz_conf['server']
        self._uri = self._server + bz_conf['rest_slug']
        self._user = bz_conf['user']
        self._passwd = bz_conf['password']
        self._auth_data = []

        self.opener = urllib.request.build_opener()

        pwmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        pwmgr.add_password(realm=None, uri=self._uri, user=self._user,
                passwd=self._passwd)
        self.opener.add_handler(urllib.request.HTTPBasicAuthHandler(pwmgr))

    def login(self):
        body = urllib.parse.urlencode({'Bugzilla_login': self._user,
                                 'Bugzilla_password': self._passwd,
                                 'GoAheadAndLogIn': 'Log+in'})
        opener = urllib.request.build_opener()
        req = urllib.request.Request(self._server, body)
        req.add_header('Accept', 'text/plain')
        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_data(body)

        # Open the connection
        resp =  opener.open(req)

        # Get the cookies
        headers = resp.info().getallmatchingheaders("Set-Cookie")
        cookies = {}
        for head in headers:
            head = head.split(":")[1] # > cookie data
            head.lstrip() # remove leading whitespace
            head = head.split(";")[0] # > 1st key=value
            key, value = head.split("=") # > key, value
            cookies[key.strip()] = value.strip()
        if "Bugzilla_login" in cookies:
            self._auth_data = [("userid", cookies["Bugzilla_login"]),
                    ("cookie", cookies["Bugzilla_logincookie"])]
        else:
            print("Did not get login cookie, using plain auth")
            self._auth_data = [("username", self._user),
                    ("password", self._passwd)]


    def __http_call(self, path, method="GET", query=None, data=None):
        """Make a HTTP call and return the retrieved object."""
        if method not in ("GET", "POST", "PUT"):
            raise ValueError("Unknown method %s" % method)
        if method == "GET" and data:
            raise TypeError("GET does not take data")
        
        if query is None:
            query = []
        query.extend(self._auth_data)

        scheme, netloc, basepath, _, _ = urllib.parse.urlsplit(self._uri)
        url = urllib.parse.urlunsplit((
            scheme, netloc, urllib.parse.urljoin(basepath, path),
            urllib.parse.urlencode(query), None))
        
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        req.get_method = lambda: method
        if data:
            req.add_data(json.dumps(data))
        try:
            resp = self.opener.open(req).read()
        except urllib.error.HTTPError as exc:
            if exc.getcode() == 400:
                resp = exc.read()
            else:
                raise
        try:
            return json.loads(resp)
        except ValueError as exc:
            raise BugzillaError(None, "Bad response from %s:\n%s" % (url, resp))

    
    def __check_error(self, result):
        """If call result was an error, raise it."""
        if result.get("error"):
            code = result.get("code")
            if not code:
                msg = str(result)
            else:
                msg = result.get("message",
                        "https://wiki.mozilla.org/Bugzilla:WebServices:Errors")
            raise BugzillaError(code, msg)


    def bug_get(self, bug_id):
        bug = self.__http_call("bug/%s" % bug_id)
        self.__check_error(bug)
        return bug

    def bug_update(self, data):
        bug_id = data.get("id")
        if not bug_id:
            raise BugzillaError(None, "Bug ID required for update")
        if not data.get("token"):
            bug = self.bug_get(bug_id)
            bug.update(data)
        else:
            bug = data
        result = self.__http_call("bug/%s" % bug_id, method="PUT", data=bug)
        self.__check_error(result)

    def comment_add(self, bug_id, message, is_private):
        comment = {"text": message, "is_private": is_private}
        result = self.__http_call("bug/%s/comment" % bug_id, method="POST",
                data=comment)
        self.__check_error(result)
