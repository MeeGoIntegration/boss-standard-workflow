# ***** BEGIN LICENCE BLOCK *****
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# version 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301 USA
# ***** END LICENCE BLOCK *****
"""
Client for sending files to qa-reports
"""
import os
import shutil
import json
import codecs
import mimetypes, mimetools, urllib2
import socket
socket.setdefaulttimeout(600)

# Based on http://code.activestate.com/recipes/146306/ By Wade Leftwich
# with minor modifications

def post_multipart(apiurl, selector, fields, files,
                   user="",
                   password="",
                   realm=""):
    """
    Post fields and files to an http host as multipart/form-data.
    
    @type apiurl: C{str}
    @param apiurl: receiving host
    
    @type selector: C{str}
    @param selector: selector part of url
    
    @type fields: C{list} of (C{str}, ?) C{tuple}s
    @param fields: sequence of (name, value) elements for regular form fields.
    
    @type files: C{list} of (C{str}, C{str}, ?) C{tuple}s
    @param files: sequence of (name, filename, value) elements for data to be
                  uploaded as files
    
    @type user: C{str}
    @param user: user name to be used in authentication
    
    @type password: C{str}
    @param password: password to be used in authentication
    
    @type realm: C{str}
    @param realm: realm to be associate with
    
    @rtype: C{file}
    @return: the server's response page.
    """
    proxy = None
    #FIXME: Detect proxy from env
    if proxy:
        proxy_support = urllib2.ProxyHandler({'https': proxy,
                                              'http': proxy})
        opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    if (user and password and realm):
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm, apiurl, user, password)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)

    content_type, body = encode_multipart_formdata(fields, files)
    headers = {'Content-Type': content_type,
               'Content-Length': str(len(body))}
    request = urllib2.Request("%s/%s" % (apiurl, selector),
                              body, headers)
    response = urllib2.urlopen(request, )
    return response.read()

def encode_multipart_formdata(fields, files):
    """
    @type fields: C{list} of ({C{str}, ?) C{tuple}s
    @param fields: sequence of (name, value) elements for regular form fields.
    
    @type files: C{list} of (C{str},C{str},?) C{tuple}s
    @param files: sequence of (name, filename, value) elements for data to be
                  uploaded as files
    
    @rtype: (C{str},C{str}) C{tuple}
    @return: tuple of content type and encoded body 
    """
    unique_boundary = mimetools.choose_boundary()
    crlf = '\r\n'
    lines = []
    for (key, value) in fields:
        lines.append('--' + unique_boundary)
        lines.append(('Content-Disposition: form-data; name="%s"' % key).encode('utf-8'))
        lines.append('')
        lines.append(value.encode('utf-8'))
    for (key, filename, value) in files:
        lines.append('--' + unique_boundary)
        lines.append(('Content-Disposition: form-data; name="%s"; filename="%s"'\
                     % (key, filename)).encode('utf-8'))
        lines.append(('Content-Type: %s' % get_content_type(filename)).encode('utf-8'))
        lines.append('Content-Transfer-Encoding: %s' % 'binary')
        lines.append('')
        lines.append(value)
    lines.append('--' + unique_boundary + '--')
    lines.append('')
    body = crlf.join(lines)
    content_type = 'multipart/form-data; boundary=%s' % unique_boundary
    return content_type, body

def get_content_type(filename):
    """
    Get content type
    """
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def _generate_form_data(result_xmls,
                        attachments = None,
                        upload_attachments = True):
    """
    Generates a form_data list from input files
    """
    if not result_xmls:
        raise ValueError("No Result xmls.")
    if attachments == None:
        attachments = []
    files = []
    index = 0
    for result in result_xmls:
        index += 1
        files.append(("report.%s" % index, result[0], result[1]))
    index = 0
    if not upload_attachments:
        return files
    for attachment in attachments:
        index += 1
        files.append(("attachment.%s" % index, attachment[0], attachment[1]))
    return files

def get_results_files_list(results_dir):

    results = []
    for root, dirs, files in os.walk(results_dir):
        for fil in files:
            results.append(os.path.join(root, fil))
    return results

def move_results_dir(results_dir, report_id):
    new_dir = os.path.join(os.path.dirname(os.path.realpath(results_dir)), "results.%s" % report_id)
    shutil.move(results_dir, new_dir)

class ReportUploader(object):

    def __init__(self, apiurl, auth_token, user, password, realm):
        self.apiurl = apiurl
        self.auth_token = auth_token
        self.user = user
        self.password = password
        self.realm = realm

    def send_files(self, result_xmls,
                   attachments,
                   hwproduct=None,
                   testtype=None,
                   target=None,
                   release_version = None,
                   build = "",
                   report_id = None):
        """
        Sends files to reporting tool
    
        @type result_xmls: C{list} of C{tuple}s consisting of 2 C{str}s
        @param result_xmls: Result xmls in format ("filename", "file content")
    
        @type attachments: C{list} of C{tuple}s consisting of 2 C{str}s
        @param attachments: Attachment files in format ("filename", "file content")
    
        @type hwproduct: C{str}
        @param hwproduct: HW product used in the report. If None, read from config
    
        @type testtype: C{str}
        @param testtype: Test Type used in the report. If None, read from config
    
        @type target: C{str}
        @param target: Target used in the report. If None, read from config
    
        @type release_version: C{str}
        @param release_version: Release_Version used in the report. If None, read
                                from config

        @type build: C{str}
        @param build: build

        @type report_id: C{str}
        @param report_id: report_id to update
        """

        selector = "import"
        if report_id:
            selector = "update/%s" % report_id

        fields = [("auth_token", self.auth_token),]
        if selector == "import":
              fields.extend([("release_version", release_version),
                            ("target", target),
                            ("testtype", testtype),
                            ("hwproduct", hwproduct),
                            ("build_txt", build)])
        
        files = _generate_form_data(result_xmls, attachments)
        
        print "Uploading results to Meego QA-reports tool: %s" % self.apiurl
        
        response = ""
        
        try:
            response = post_multipart(self.apiurl, selector, fields, files,
                                      self.user, 
                                      self.password,
                                      self.realm)
    
            json_response = json.loads(response)
            
            if json_response.get("ok") == "1":
                url = json_response.get("url", "")
                print "Results uploaded successfully %s" % url
                msg = "Results uploaded successfully %s" % url
                return url, msg
            else:
                print "Upload failed. Server returned: %s" % response
                msg = "Upload failed. Server returned: %s" % response
                return "", msg
    
        except urllib2.HTTPError:
            print "Invalid url or authentication failed"
            raise
                
        except ValueError:
            print "Invalid JSON response:\n%s" % response
            raise

