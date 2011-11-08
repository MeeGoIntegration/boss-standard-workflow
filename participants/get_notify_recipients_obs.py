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
   ev(dictionary):
      Dictionary representing the OBS event that triggered the current process.
      http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List

:term:`Workitem` params IN

:Parameters:
   roles(list of string):
      Tokens that describe users from the ev field to look up in OBS and add.
      Supported tokens: "submitter", "target project maintainers"
   role(string):
      A single role token
   users(list of string):
      Users to look up in OBS and add.
   user(string):
      Single user to look up in OBS and add.
   maintainers_of(string):
      Name of OBS project; look up and add all its project maintainers.
   cc(boolean):
      Add users to Cc list instead of To list.

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

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        if not wid.fields.ev or not wid.fields.ev.namespace:
            raise RuntimeError("Missing mandatory field 'ev.namespace'")

        users = set(wid.params.users or [])
        if wid.params.user:
            users.add(wid.params.user)

        roles = set(wid.params.roles or [])
        if wid.params.role:
            roles.add(wid.params.role)

        maintainers_of = set()
        if wid.params.maintainers_of:
            maintainers_of.add(wid.params.maintainers_of)

        if not users and not roles and not maintainers_of:
            raise RuntimeError("None of paramters 'user', 'role' or "
                    "'maintainers_of' specified. Nothing to do")

        # Process roles by adding to 'users' and 'maintainers_of'
        for role in roles:
            if role == "submitter":
                if not wid.fields.ev.who:
                    raise RuntimeError("Submitter not found in field 'ev.who'")
                users.add(wid.fields.ev.who)
            elif role == "target project maintainers":
                if not wid.fields.ev.actions:
                    raise RuntimeError("Field 'ev.actions' needed for role "
                            "'target project maintainers'")
                maintainers_of.update(action["targetproject"]
                                      for action in wid.fields.ev.actions
                                      if "targetproject" in action)
            else:
                raise RuntimeError("Unknown role token: %s" % role)

        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)

        # Process maintainers_of by adding to 'users'
        for project in maintainers_of:
            try:
                users.update(obs.getProjectPersons(project, 'maintainer'))
            except urllib2.HTTPError, exc:
                # probably means project does not exist
                raise RuntimeError("Could not look up project '%s': %d %s" %
                        (project, exc.getcode(), exc.geturl()))

        # Now all users to notify are in 'users'

        if wid.params.cc:
            mailaddr = set(wid.fields.mail_cc or [])
        else:
            mailaddr = set(wid.fields.mail_to or [])

        for user in users:
            try:
                addr = obs.getUserData(user, 'email')[0]
            except IndexError:
                message = "Could not notify %s (no address found)" % user
                if message not in wid.fields.msg:
                    wid.fields.msg.append(message)
                continue
            mailaddr.add(addr)

        if wid.params.cc:
            wid.fields.mail_cc = list(mailaddr)
        else:
            wid.fields.mail_to = list(mailaddr)

        wid.result = True
