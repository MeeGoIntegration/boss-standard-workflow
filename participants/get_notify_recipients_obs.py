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
   recipients(list of string):
      Names of users, groups or projects to look up in OBS. The type will be
      figured out automatically
   recipient(string):
      The name of a user, group or project to look up in OBS. The type will
      be figured out automatically
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
import re
import urllib2
from boss.obs import BuildServiceParticipant

class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """Job control thread"""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Handle a workitem: look up addresses"""

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        users = set(wid.params.users or [])
        if wid.params.user:
            users.add(wid.params.user)

        roles = set(wid.params.roles or [])
        if wid.params.role:
            roles.add(wid.params.role)

        maintainers_of = set()
        if wid.params.maintainers_of:
            maintainers_of.add(wid.params.maintainers_of)

        recipients = set(wid.params.recipients or [])
        if wid.params.recipient:
            recipients.add(wid.params.recipient)

        if wid.params.cc:
            mailaddr = set(wid.fields.mail_cc or [])
        else:
            mailaddr = set(wid.fields.mail_to or [])

        for recipient in recipients:
            etype = self.obs.getType(recipient)
            if etype == "unknown":
                continue
            elif etype == "person":
                users.add(recipient)
            elif etype == "group":
                users.update(self.obs.getGroupUsers(recipient))
            elif etype == "project":
                maintainers_of.add(recipient)

        if not users and not roles and not maintainers_of:
            msg = ""
            if recipients:
                msg = "Specified unknown recipients: %s and " % ",".join(recipients)
            msg = "%snone of parameters 'user', 'role' or 'maintainers_of'"\
                  " specified." % msg

            raise RuntimeError(msg)

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
                     if action.get("targetproject"))
            elif role == "last author":
                emailre = re.compile("(?P<email><[^>]+>)")
                for action in wid.fields.ev.actions:
                    found = False
                    for entry in action.get("relevant_changelog", ""):
                            for addr in emailre.findall(entry):
                                addr = addr.replace("<","").replace(">","")
                                mailaddr.add(addr)
                                found = True
                            if found: break
            else:
                raise RuntimeError("Unknown role token: %s" % role)

        # Process maintainers_of by adding to 'users'
        for project in maintainers_of:
            try:
                users.update(self.obs.getProjectPersons(project, 'maintainer'))
            except urllib2.HTTPError, exc:
                # probably means project does not exist
                raise RuntimeError("Could not look up project '%s': %d %s" %
                        (project, exc.getcode(), exc.geturl()))

        # Now all users to notify are in 'users'
        for user in users:
            addr = self.obs.getUserEmail(user)
            if not addr:
                message = "Could not notify %s (no address found)" % user
                if message not in wid.fields.msg:
                    wid.fields.msg.append(message)
                continue
            mailaddr.add(addr)

        if not mailaddr and wid.params.fallback:
            mailaddr.add(wid.params.fallback)

        if wid.params.cc:
            wid.fields.mail_cc = list(mailaddr)
        else:
            wid.fields.mail_to = list(mailaddr)

        wid.result = True
