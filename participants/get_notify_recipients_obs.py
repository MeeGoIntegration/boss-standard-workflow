"""Email notification selection participant
This participant looks up email addresses in obs in order to add them to
the notification lists.

If a user is unknown or does not have an address listed then this is
reported in the msg list.

If a project is unknown or cannot be looked up then it's raised as
a process error.

:term:`Workitem` fields IN

:Parameters:
   mail_to(list of string):
      Optional. Previously specified recipient addresses.
      New ones will be added to this.
   mail_cc(list of string):
      Optional. Previously specified Cc addresses.
      New ones will be added to this if cc param is set.

:term:`Workitem` params IN

:Parameters:
   users(list of string):
      Users to look up in OBS and add
   user(string):
      Single user to look up in OBS and add
   maintainers_of(string):
      Name of OBS project; look up and add all its project maintainers
   cc(boolean):
      Add users to Cc list instead of To list

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if everything went OK, False otherwise
   msg(list of string):
      Error messages
   mail_to(list of string):
      Recipient addresses
   mail_cc(list of string)
      Recipient addresses if cc param is set
"""

import urllib2

from buildservice import BuildService
import ConfigParser

class ParticipantHandler(object):
    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """Job control thread"""
        pass

    def handle_lifecycle_control(self, ctrl):
        """ :param ctrl: Control object passed by the EXO.
            :type ctrl: SkyNET.Control.WorkItemCtrl object
        """
        if ctrl.message == "start":
            try:
                self.oscrc = ctrl.config.get("obs", "oscrc")
            except ConfigParser.Error, err:
                raise RuntimeError("Participant configuration error: %s" % err)

    def handle_wi(self, wid):
        """Handle a workitem: look up addresses"""
        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        if not wid.fields.ev or not wid.fields.ev.namespace:
            wid.error = "Missing mandatory field ev.namespace"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        if not (wid.params.user or wid.params.users\
                or wid.params.maintainers_of):
            wid.error = "At least one of user, users or "\
                        " maintainers_of is required."
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        users = wid.params.users or []
        if wid.params.user:
            users.append(wid.params.user)

        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)

        if wid.params.maintainers_of:
            try:
                maintainers = obs.getProjectPersons(wid.params.maintainers_of,
                                                    'maintainer')
                users.extend(maintainers)
            except urllib2.HTTPError:
                # probably means project does not exist
                wid.error = "Could not look up project %s" \
                            % wid.params.maintainers_of
                wid.fields.msg.append(wid.error)
                raise

        if wid.params.cc:
            mailaddr = wid.fields.mail_cc or []
        else:
            mailaddr = wid.fields.mail_to or []

        for user in users:
            try:
                addr = obs.getUserData(user, 'email')[0]
            except IndexError:
                message = "Could not notify %s (no address found)" % user
                if message not in wid.fields.msg:
                    wid.fields.msg.append(message)
                continue
            if addr not in mailaddr:
                mailaddr.append(addr)

        if wid.params.cc:
            wid.fields.mail_cc = mailaddr
        else:
            wid.fields.mail_to = mailaddr

        wid.result = True
