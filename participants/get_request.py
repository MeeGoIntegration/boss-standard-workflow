#!/usr/bin/python
""" Participant to get information about an OBS request.

    The request data is placed into a specified field.

    example::

      get_request :req_id => "1854", :field => "req.curr"

    Will result in the fields in ${req.curr} being populated:

    The request detail is defined in the OBS; a sample is shown below.

    *Parameter fields IN :*

    :param req_id: The request for which information is required
    :type req_id: integer

    :param field: Field to populate with request details
    :type field: string

    :param no_diff: Normally get_result will calculate 'diff' information for
                    each action. Use this option to turn that off.
    :type no_diff: true/false (default false)

    *Workitem fields OUT :*

    :returns $field.*: Request information
    :rtype $field.fullname: complex

    complex example ::

        "req": {
            "actions": [
                {
                    "diff": "",
                    "source": {
                        "package": "",
                        "project": "",
                        "rev": ""
                    },
                    "target": {
                        "package": "",
                        "project": ""
                    },
                    "type": "submit"
                },
                {
                    "diff": "",
                    "source": {
                        "package": "",
                        "project": "",
                        "rev": ""
                    },
                    "target": {
                        "package": "",
                        "project": ""
                    },
                    "type": "submit"
                }
            ],
            "description": "",
            "id": "",
            "reviews": [
                {
                    "by_user": "",
                    "comment": "",
                    "state": "accepted",
                    "when": "2011-09-29T11:03:11",
                    "who": ""
                },
                {
                    "by_user": "",
                    "comment": "",
                    "state": "new"
                }
            ],
            "state": {
                "comment": "",
                "name": "review",
                "state": "state",
                "when": "2011-09-29T11:03:12",
                "who": ""
            },
            "statehistory": [
                {
                    "name": "new",
                    "state": "history",
                    "when": "2011-09-29T11:03:09",
                    "who": ""
                },
                {
                    "comment": "",
                    "name": "review",
                    "state": "history",
                    "when": "2011-09-29T11:03:10",
                    "who": ""
                },
                {
                    "comment": "",
                    "name": "new",
                    "state": "history",
                    "when": "2011-09-29T11:03:11",
                    "who": ""
                }
            ]
        }


"""

from boss.obs import BuildServiceParticipant
from osc import core


def assertMandatoryParameter(wid, param):
    if (
        param not in wid.params.as_dict() or
        wid.params.as_dict()[param] is None
    ):
        raise RuntimeError("Mandatory parameter: ':%s' not provided" % param)
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

    def get_request(self, wid, req_id, diff):
        # Copied from api.py
        req = core.get_request(self.obs.apiurl, req_id)
        return self.obs.req_to_dict(req, action_diff=diff)

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ """

        req_id = assertMandatoryParameter(wid, "req_id")
        field = assertMandatoryParameter(wid, "field")

        # the result, in unicode string
        diff = False if wid.params.no_diff else True
        wid.set_field(field, self.get_request(wid, req_id, diff))
