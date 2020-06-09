"""
OTS specific functions used by the OTS Participant
(separated into a different file to make testing easier)
"""

import xmlrpc.client

def parse_options(wid):
    """
    Parses ots specific options from BOSS workitem

    @type wid: C{Workitem}
    @param wid: Boss Participant Workitem
    
    @rtype: C{tuple} consisting of C{string}, C{string}, C{list} and C{dict}
    @return: A tuple containing sw_product, build_id, email_list and ots_options
    """
    sw_product = wid.fields.product
    build_id = wid.fields.rid
    email_list = wid.fields.emails
    ots_options = { 'image' : wid.fields.image.image_url,
                    'device' : wid.fields.image.devicegroup
                  }

    if wid.fields.image.test_options:
        ots_options.update(wid.fields.image.test_options.as_dict())

    return (sw_product, build_id, email_list, ots_options)


def call_ots_server(server,
                    sw_product,
                    build_id,
                    email_list,
                    options,
                    debug=False,
                    ots_interface = None):
    """
    triggers a testrun by calling ots server xmlrpc interface

    @type server: C{string}
    @param server: The url to ots server xmlrpc interface

    @type build_id: C{string}
    @param build_id: Unique identifier for the build

    @type email_list: C{list}
    @param email_list: List of email addresses

    @type options: C{dict}
    @param options: A dictionary containing additional OTS options

    @type options: C{OTS xmlrpclib Server interface}
    @param options: OTS xmlrpc interface server. If None, the default server \
			will be created
    
    @rtype: C{string}
    @return: Testrun overall result (PASS/FAIL/ERROR)
    """

    print("Server url set to %s" % server)
    print("Parameters:")
    print("sw_product: %s" % sw_product)
    print("build_id: %s" % build_id)
    print("email_list: %s" % email_list)
    print("options: %s" % options)

    if not debug:
        if not ots_interface:
            ots_interface = xmlrpc.client.Server(server)

        print("calling OTS server")
        result = ots_interface.request_sync(sw_product,
                                            build_id,
                                            email_list,
                                            options)

        print("OTS server returned %s" % result)

    else:
        print("Debug mode. Not calling OTS server. Result set to ERROR.")
        result = "ERROR"
    return result
