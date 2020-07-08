#!/usr/bin/python3
""" Participant to get a person's userdata from an OBS instance.

    The user data is placed into a specified field.

    example::

      get_userdata :user => "lbt", :field => "role.author"

    Will result in the two fields ${role.author.email} and
    ${role.author.realname} being populated.

    *Parameter fields IN :*

    :param user: The user login id
    :type user: string

    :param field: Field to populate
    :type field: string

    *Workitem fields OUT :*

    :returns $field.realname: Real name of user or empty if not available
    :rtype $field.fullname: string

    :returns $field.email: Email address of user or empty if not available
    :rtype $field.email: string

"""

from buildservice import BuildService
import functools

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

    @classmethod
    def assertMandatoryParameter(cls, wid, param):
        if param not in wid.params.as_dict() or wid.params.as_dict()[param] is None:
            raise RuntimeError("Mandatory parameter: ':%s' not provided" % param)
        return wid.params.as_dict()[param]

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def handle_wi(self, wid):
        """ """

        self.setup_obs(wid.fields.ev.namespace)
        user = Verify.assertMandatoryParameter(wid, "user")
        field = Verify.assertMandatoryParameter(wid, "field")

        user_realname, user_email = self.obs.getUserData(user, "realname", "email")

        wid.set_field(field + ".realname", user_realname)
        wid.set_field(field + ".email", user_email)
