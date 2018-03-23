#!/usr/bin/env python
"""
Participant for uploading test results to QA-reports tool

:term:`Workitem` fields IN

:Parameters:
    results_dir(string):
        Path to the directory containing the report XML files and any other
        attachments
    move_results(boolean):
        If true moves the results files to results_dir/<report id> after
        uploading the them
    report_id(integer):
        If set, updates existing report instead of creating a new one

:term:`Workitem` params IN

:Parameters:
    qa.hwproduct(string):
        Passed to QA-reports as hwproduct parameter
    qa.testtype(string:
        Passed to QA-reports as testtype parameter
    qa.target(string):
        Passed to QA-reports as target parameter
    qa.release_version(string):
        Passed to QA-reports as release_version parameter
    image.image_url(string):
        Passed to QA-reports as build_txt parameter

:term:`Workitem` fields OUT

:Returns:
    qa.results.report_url(string):
        URL of the created report

"""
import mimetypes
import os
import shutil

import requests


class ParticipantHandler(object):
    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self._apiurl = ctrl.config.get("qareports", "apiurl")
            self._auth_token = ctrl.config.get("qareports", "auth_token")
            user = ctrl.config.get("qareports", "user")
            password = ctrl.config.get("qareports", "password")
            if user and password:
                self._auth = (user, password)
            else:
                self._auth = None

    def handle_wi(self, wid):

        results_dir = wid.params.results_dir
        if not results_dir:
            if (
                wid.fields.test_execution_exit_status and
                wid.fields.test_execution_exit_status.results_dir
            ):
                # Only for Backwards compatibility
                results_dir = wid.fields.test_execution_exit_status.results_dir
                self.log.warn(
                    "Using deprecated field "
                    "test_execution_exit_status.results_dir"
                )
            else:
                self.log.error("No results_dir defined")
                return

        file_list = list_files(results_dir)
        if not file_list:
            self.log.info("No files in results dir %s", results_dir)
            return

        url, msg = self.upload(
            file_list=file_list,
            import_params=dict(
                hwproduct=wid.fields.qa.hwproduct,
                testtype=wid.fields.qa.testtype,
                target=wid.fields.qa.target,
                release_version=wid.fields.qa.release_version,
                build_txt=wid.fields.image.image_url,
            ),
            report_id=wid.params.report_id,
        )

        if url:
            if not wid.fields.qa.results:
                wid.fields.qa.results = {}
            wid.fields.qa.results.report_url = url

            if wid.params.move_results:
                report_id = os.path.basename(url)
                move_results_dir(results_dir, report_id)

        if msg:
            if not wid.fields.msg:
                wid.fields.msg = []
            wid.fields.msg.append(msg)

    def upload(self, file_list=None, import_params=None, report_id=None):
        params = dict(auth_token=self._auth_token)
        if report_id:
            selector = "update/%s" % report_id
        else:
            selector = "import"
            params.update(import_params)

        result_index = 1
        attachment_index = 1
        files = {}
        for file_name in file_list:
            if file_name.endswith(".xml"):
                key = "report.%s" % result_index
                result_index += 1
            else:
                key = "attachment.%s" % attachment_index
                attachment_index += 1
            files[key] = [
                file_name, open(file_name, 'rb'), get_content_type(file_name)
            ]

        self.log.info(
            "Uploading results to QA-reports tool: %s", self._apiurl
        )

        response = requests.post(
            '%s/%s' % (self._apiurl, selector),
            files=files,
            data=params,
            auth=self._auth,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("ok") == "1":
            url = result.get("url", "")
            msg = "Results uploaded successfully %s" % url
            self.log.info(msg)
            return url, msg
        else:
            msg = "Upload failed. Server returned: %s" % response.content
            self.log.error(msg)
            return "", msg


def list_files(directory):
    """Return list of files in directory, with full path"""
    results = []
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            results.append(os.path.join(root, file_name))
    return results


def move_results_dir(results_dir, report_id):
    """Move results_dir to <results_dir>/../results.<report_id>"""
    new_dir = os.path.join(
        os.path.dirname(os.path.realpath(results_dir)),
        "results.%s" % report_id,
    )
    shutil.move(results_dir, new_dir)


def get_content_type(filename):
    """Get file content type"""
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
