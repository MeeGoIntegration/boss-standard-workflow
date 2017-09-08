from qarep.upload import *

class ParticipantHandler(object):
    def handle_wi_control(self, ctrl):
        pass

    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            apiurl = ctrl.config.get("qareports", "apiurl")
            auth_token = ctrl.config.get("qareports", "auth_token")
            user = ctrl.config.get("qareports", "user")
            password = ctrl.config.get("qareports", "password")
            realm = ctrl.config.get("qareports", "realm")
            self.uploader = ReportUploader(apiurl, auth_token, user, password, realm)

    def handle_wi(self, wid):

        f = wid.fields
        p = wid.params

        hwproduct = f.qa.hwproduct
        testtype = f.qa.testtype
        target = f.qa.target
        release_version = f.qa.release_version
        build = f.image.image_url

        if not f.qa or not f.qa.results:
            self.log.info("no results in this workitem")
            return
        results = get_results_files_list(f.qa.results.results_dir)

        attachments = []
        result_xmls = []

        for result in results:
            if result.endswith(".xml"):
                result_contents = open(result).read()
                if result_contents.strip().startswith("<"):
                    result_xmls.append((result, result_contents))
                else:
                    attachments.append((result, result_contents))
            else:
                attachments.append((result, open(result).read()))

        if result_xmls:
            url, msg = self.uploader.send_files(result_xmls,
                                                attachments,
                                                hwproduct=hwproduct,
                                                testtype=testtype,
                                                target=target,
                                                release_version = release_version,
                                                build = build)

            wid.fields.qa.results.report_url = url
            if url and ((f.qa and f.qa.move_results) or (p.move_results)):
                move_results_dir(f.qa.results.results_dir, os.path.basename(url))

            if not wid.fields.msg:
                wid.fields.msg = []

            wid.fields.msg.append(msg)
