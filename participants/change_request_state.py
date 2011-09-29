#!/usr/bin/python
"""Change the state of a submit request to either accepted or declined.

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the trial build project.

:term:`Workitem` fields IN:

:Parameters:
   ev.id:
      Submit request id

:term:`Workitem` params IN

:Parameters:
   action(string):
      The action to be performed on the submit request :
      Either "accept" or "decline".

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from buildservice import BuildService
from urllib2 import HTTPError

class Verify:
    """ Small verification class """

    def __init__(self):
        pass

    @classmethod
    def assertNotNull(cls, desc, value):
        """ Asserts a variable is not None or empty """
        if not value:
            raise RuntimeError(desc)

    @classmethod
    def assertEqual(cls, desc, value1, value2):
        """ Asserts two variables are equal """
        if value1 != value2:
            raise RuntimeError(desc)

class ParticipantHandler(object):

    """Participant class as defined by the SkyNET API."""

    def __init__(self):
        self.oscrc = None
        self.obs = None

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """Setup the Buildservice instance.

        Using the namespace as an alias to the apiurl.
        """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def handle_request(self, wid):
        """Request handling implementation."""

        wid.result = False
        if not wid.fields.msg :
            wid.fields.msg = []
        rid = str(wid.fields.ev.id)

        # https://api.opensuse.org/apidocs/request.xsd
        newstate = None
        if wid.params.action == 'accept':
            newstate = "accepted"
        elif wid.params.action == 'reject' or wid.params.action == 'decline' :
            newstate = "declined"

        Verify.assertNotNull("Request ID field must not be empty", rid)
        Verify.assertNotNull(
            "Participant action should be accept, reject or decline",
            newstate)

        msgstring = "Bossbot %s this request because: %s" % (
            newstate, "\n ".join(wid.fields.msg) )

        try:
            res = self.obs.setRequestState(rid, newstate, msgstring)
            if res:
                print "%s request %s" % (newstate , rid)
                wid.result = True
            else:
                print "Failed to %s request %s" % (wid.params.action , rid)
        except HTTPError, exc:
            if exc.code == 403:
                wid.fields.msg.append("Applying the actions required to"
                                      " automate this process has failed,"
                                      " because the %s user was not authorized"
                                      " to do so."
                                      " Please add %s as a maintainer in the"
                                      " target project %s" %
                                      (self.obs.getUserName(),
                                       self.obs.getUserName(),
                                       wid.fields.project))
                print "Forbidden to %s request %s" % (wid.params.action, rid)
            elif exc.code == 401:
                wid.fields.msg.append("Credentials for the '%s' user were"
                                      " refused. Please update the skynet"
                                      " configuration." %
                                      self.obs.getUserName())
                print exc
                print "User is %s" % self.obs.getUserName()
            else:
                import traceback
                print exc
                traceback.print_exc()
                raise


    def handle_wi(self, wid):
        """Actual job thread."""

        # We may want to examine the fields structure
        if wid.fields.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.handle_request(wid)
