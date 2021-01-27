#!/usr/bin/python
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

from boss.obs import BuildServiceParticipant


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
        if (
                param not in wid.params.as_dict() or
                wid.params.as_dict()[param] is None
        ):
            raise RuntimeError(
                "Mandatory parameter: ':%s' not provided" % param
            )
        return wid.params.as_dict()[param]


class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ """

        user = Verify.assertMandatoryParameter(wid, "user")
        field = Verify.assertMandatoryParameter(wid, "field")

        user_realname, user_email = self.obs.getUserData(
            user, "realname", "email"
        )

        wid.set_field(field + ".realname", user_realname)
        wid.set_field(field + ".email", user_email)
