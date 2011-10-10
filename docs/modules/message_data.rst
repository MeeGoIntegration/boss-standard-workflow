OTS Message_data
================

Note! This is not an interface definition. It just documents the most important 
parts of the current behavior!

Expected input
**************

    sw_product = workitem.lookup("product") # Sw product name as a string
    build_id = workitem.lookup("id") # Build Id as a string
    email = workitem.lookup("email") # List of email address strings
    image = workitem.lookup("image") # See below
    packages = workitem.lookup("packages")
    device = workitem.lookup("device")

ots_options dictionary
**********************


ots_options["image"]    # A string containing the url to the image (mandatory)
ots_options["packages"] # A string of testpackage names (optional)
for example: "pkg1-tests pkg2-tests pkg3-tests"

ots_options["device"]  # A string specifying the device parameters required for the testrun. Currently only devicegroup is supported
example: ots_options["device"] = "devicegroup:mygroup"

ots_options["email"]   # A string. If "off" ots won't send the result email Default: "on"

ots_options["email-attachments"]   # A string. If "on" all result files will be sent as a zip file attachment. Default: "off"



ots_options["execute"] # A string. If "false", ots will return "ERROR" without starting any testruns


ots_options["testfilter"] # Test filtering option string for testrunner-lite
see http://wiki.meego.com/Quality/QA-tools/Testrunner-lite for more details




Output
******

self.workitem.set_field("testrun_result", result) # The overall testrun result
                                                  # "PASS"/"FAIL"/"ERROR"
