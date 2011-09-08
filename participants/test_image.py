#!/usr/bin/python
"""
This paticipant acts as a proxy to an OTS system. It sends an XMLRPC request,
with the needed parameters and waits for the test results.

... warning::
    the build_image participant must be run first to create an image and provide
    its information in the workitem.

:term:`Workitem` fields IN

:Parameters:
    product(string):
       The product name used in OTS
    rid(string):
       The request id
    emails(list):
       emails the OTS server will send notification to
    image.image_url(string):
       URL to the image the OTS server will download over HTTP
    image.devicegroup(string):
       Name of the OTS devicegroup that will be used for testing
    image.test_options(dict):
       key : value pairs of extra options that will be passed to OTS, for
       example {"flasher":"http://urltoflasher"}

:term:`Workitem` params IN

:Parameters:
    enforce(string):
       By default the test result returned by OTS is taken into account
       for the participant return status. if this parameter is set to "False",
       the test result is ignored.

:term:`Workitem` fields OUT

:Returns:
    image.test_result(string):
       The test result as returned by OTS
    result(boolean):
       if OTS returns "PASS" this is True, otherwise False.

"""
import ots.ots_connector

class ParticipantHandler(object):
    """Participant for passing an image URL to OTS test service and running
    tests on it.
    """
    def __init__(self):
        self.ots_server = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            self.ots_server = ctrl.config.get("test_image", "ots_server_url")

    def handle_wi(self, wid):
        """Parse workitem and passs the parameters to OTS for testing."""

        wid.result = False

        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        if not wid.fields.msg:
            wid.fields.msg = []

        # debug turned off by default
        debug = False
        if wid.fields.debug and wid.fields.debug == "True" :
            debug = True

        # enforce turned on by default
        enforce = True
        if wid.params.enforce:
            if wid.params.enforce == "False":
                enforce = False

        sw_product, build_id, email_list, options = \
            ots.ots_connector.parse_options(wid.fields)

        result = ots.ots_connector.call_ots_server(self.ots_server,
                                                   sw_product,
                                                   build_id,
                                                   email_list,
                                                   options,
                                                   debug)

        wid.fields.image.ots_result = result
        wid.fields.msg.append('OTS testing results: %s' % (result))

        if result == "PASS" or not enforce:
            wid.result = True

