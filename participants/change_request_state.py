#!/usr/bin/python
"""Change the state of a submit request to either accepted or declined.

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the target project of the request

:term:`Workitem` fields IN:

:Parameters:
   ev.id:
      Submit request id
   msg (list of strings):
      Accumulated messages describing the results of the various process steps
      so far, appended to the action comment

:term:`Workitem` params IN

:Parameters:
   action(string):
      The action to be performed on the submit request :
      "accept", "decline", "add review", "accept review", "decline review"
   comment(string):
      Short explanation of the reason the state change is being performed
   user (string):
      OBS username to ask for review
   group (string):
      OBS groupname to ask for review

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from boss.obs import BuildServiceParticipant
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


class ParticipantHandler(BuildServiceParticipant):
    """Participant class as defined by the SkyNET API."""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        rid = str(wid.fields.ev.id)

        # https://api.opensuse.org/apidocs/request.xsd
        obj_type = "request"
        newstate = None
        if wid.params.action == 'accept':
            newstate = "accepted"
        elif wid.params.action == 'reject' or wid.params.action == 'decline':
            newstate = "declined"
        elif wid.params.action == 'add review':
            obj_type = "review"
            newstate = "add"
        elif wid.params.action == 'accept review':
            obj_type = "review"
            newstate = "accepted"
        elif wid.params.action == 'decline review':
            obj_type = "review"
            newstate = "declined"

        Verify.assertNotNull("Request ID field must not be empty", rid)
        Verify.assertNotNull(
            "Participant action should be one of "
            "accept, decline, add review, accept review, decline review",
            newstate
        )

        # So sometimes it seems that the request is not available
        # immediately. In that case we wait a short while and retry
        retries = 0
        retry = True
        while retry:
            retry = False  # Only try once unless specified
            try:
                if obj_type == "review":
                    reviewer = wid.params.reviewer
                    extra_msg = ""

                    if wid.params.comment:
                        extra_msg = "%s\n" % wid.params.comment

                    if not reviewer:
                        reviewer = self.obs.getUserName()
                    if newstate == "add":
                        res = self.obs.addReview(rid, extra_msg, reviewer)
                    else:
                        res = self.obs.setReviewState(rid, newstate, extra_msg,
                                                      reviewer)
                elif obj_type == "request":

                    extra_msg = ""

                    if wid.params.comment:
                        extra_msg = "%s\n" % wid.params.comment

                    msgstring = "%sBOSS %s this %s because:\n %s" % (
                        extra_msg, newstate, obj_type,
                        "\n ".join(wid.fields.msg)
                    )

                    self.log.debug(msgstring)
                    res = self.obs.setRequestState(
                        str(rid), str(newstate), str(msgstring)
                    )

                if res:
                    self.log.info("%s %s %s", newstate, obj_type, rid)
                    wid.result = True
                else:
                    self.log.info(
                        "Failed to %s %s %s",
                        wid.params.action, obj_type, rid
                    )

            except HTTPError, exc:
                if exc.code == 403:
                    self.log.info(
                        "Forbidden to %s %s %s",
                        wid.params.action, obj_type, rid
                    )
                elif exc.code == 401:
                    wid.fields.msg.append(
                        "Credentials for the '%s' user were refused. "
                        "Please update the skynet configuration." %
                        self.obs.getUserName()
                    )
                    self.log.info(exc)
                    self.log.info("User is %s" % self.obs.getUserName())
                elif exc.code == 404:
                    # How did we get a request ID which is 404?
                    # Maybe a race thing? So retry.
                    retries += 1
                    self.log.info(exc)
                    if retries < 3:
                        import time
                        time.sleep(10)
                        retry = True
                        self.log.info(
                            "Failed Request ID is %s (retrying now)" %
                            rid)
                    else:
                        wid.fields.msg.append(
                            "Request ID '%s' doesn't seem to exist "
                            "(even after %d retries)" %
                            (rid, retries)
                        )
                        raise
                else:
                    self.log.exception('Unknown error')
                    raise
