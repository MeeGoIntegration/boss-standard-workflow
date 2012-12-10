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

"""Participant for qa-reports based voting on testresults

:term:'Workitem' fields IN:

:Parameters:
    qa.results.report_url(string):
       The url where the results of the test run are located

:term:`Workitem` params IN

:Parameters:
     ignore_new_failed(string):
         True: ignores new failed test cases, in other words if new
               test cases failes, it does not change the status Field 
         Anything else or missing: New failing test cases let the status
               set to FAILED
     ignore_removed(string):
         True: ingnore test cases which changed from FAIL to N/A
               e.g. temp. removed ones
         Anything else or missing: test cases which changed from FAIL
               to N/A let the status set to FAILED 
     verbose(string):
         True: detailed report is added to the msg array in any case
         Anything else or missing: just simple reason for FAILED is given

:term:`Workitem` fields OUT:

:Returns:
    status(string):
        changes to FAILED if there was a regression
    msg(array):
        messages worth to add to the work item
"""

import json
import urllib2

def get_reports_json(json_url,
                     user="",
                     password="",
                     realm=""):

    if (user and password and realm):
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm, json_url, user, password)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)

    request = urllib2.Request(json_url)
    response = urllib2.urlopen(request,)
    return response.read()

class ParticipantHandler(object):
    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.user = ctrl.config.get("qa_vote", "qareports", "user")
            self.password = ctrl.config.get("qa_vote", "qareports", "password")
            self.realm = ctrl.config.get("qa_vote", "qareports", "realm")
            self.reportsurl = ctrl.config.get("qa_vote", "reportsurl")

    def handle_wi(self, wid):
        f = wid.fields

        if not f.status:
            f.status = ""

        if not f.msg:
            f.msg = []

        if not f.qa.results.report_url:
            f.status = "FAILED"
            f.msg.append("No qa-reports (mandatory) url in work item, nothing to compare with")
            return

        p = wid.params
        ignore_new_failed = False
        ignore_removed = False
        verbose = False

        if p.ignore_new_failed and p.ignore_new_failed == "True":
            ignore_new_failed = True

        if p.ignore_removed and p.ignore_removed == "True":
            ignore_removed = True

        if p.verbose and p.verbose == "True":
            verbose = True
            
        url = f.qa.results.report_url
        path,sep,qareports_id = url.rpartition("/")
        reportsurl = self.reportsurl.lstrip('"')
        reportsurl = reportsurl.rstrip('"')
        json_url = "%s%s/compare/previous.json"%(reportsurl,qareports_id)

        try:
            json_report = get_reports_json(json_url, self.user, self.password, self.realm)
            json_response = json.loads(json_report)
            report = json_response['comparison']

            if verbose:
                f.msg.append("Test results compared to previous test run")
                '''Pass'''
                f.msg.append("changed_to_pass: %i"    % report['changed_to_pass'])
                f.msg.append("fixed_from_fail: %i"    % report['fixed_from_fail'])
                f.msg.append("fixed_from_na: %i"      % report['fixed_from_na'])
                '''Fail'''
                f.msg.append("changed_to_fail: %i"    % report['changed_to_fail'])
                f.msg.append("regression_to_fail: %i" % report['regression_to_fail'])
                f.msg.append("regression_to_na: %i"   % report['regression_to_na'])
                '''New'''
                f.msg.append("new_passed: %i"         % report['new_passed'])
                f.msg.append("new_failed: %i"         % report['new_failed'])
                f.msg.append("new_na: %i"             % report['new_na'])

                f.msg.append("changed_to_na: %i"      % report['changed_to_na'])

            if ignore_new_failed and not ignore_removed:
                if report['changed_to_fail'] > 0:
                    f.status = "FAILED"
                    f.msg.append("Set status to FAILED due"
                                 + " to %i test(s)"%report['regression_to_fail']
                                 + " changed from PASS to FAIL and"
                                 + " %i test(s)"%report['regression_to_na']
                                 + " changed from PASS to N/A." )
            elif ignore_removed and not ignore_new_failed:
                if report['regression_to_fail'] > 0 and report['new_failed'] > 0:
                    f.status = "FAILED"
                    f.msg.append("Set status to FAILED due"
                                 + " to %i test(s)"%report['regression_to_fail']
                                 + " changed from PASS to FAIL and"
                                 + " %i test(s)"%report['new_failed']
                                 + " are new and FAIL." )
            elif ignore_new_failed and ignore_removed:
                if report['regression_to_fail'] > 0:
                    f.status = "FAILED"
                    f.msg.append("Set status to FAILED due"
                                 + " to %i test(s)"%report['regression_to_fail']
                                 + " changed from PASS to FAIL.")
            else:    
                if report['changed_to_fail'] > 0 or report['new_failed'] > 0:
                    f.status = "FAILED"
                    f.msg.append("Set status to FAILED due"
                                 + " to %i test(s)"%report['regression_to_fail']
                                 + " changed from PASS to FAIL and"
                                 + " %i test(s)"%report['regression_to_na'] 
                                 + " changed from PASS to N/A and" 
                                 + " %i test(s)"%report['new_failed']
                                 + " are new and FAIL." )
            if f.status != "FAILED":
                f.msg.append("No regressions found compared to last test run in qa-reports")

        except urllib2.HTTPError as e:
            self.log.error('HTTP Error code: %s'%e.code)
            if e.code == 404:
                self.log.error("There is probably no previous test run or id is wrong!")
                f.msg.append("HTTP Error 404, there is probably no previous test run or id is wrong!")
                f.msg.append("No changes to status field!")
            else:
                self.log.error("Invalid url or authentication failed")
                raise

        except urllib2.URLError as e:
            self.log.error('We failed to reach a server.')
            self.log.error('Reason: %s'%e.reason)
            raise
