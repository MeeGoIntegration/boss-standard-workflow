"""
This participant is used to extract ts files from -ts-devel binary RPMs
and upload them to translation Git repositories.

:term:`Workitem` params IN

:Parameters:
    ts_urls(list):
        Optional list of urls of ts-devel rpms

:term:`Workitem` fields IN

:Parameters:
    ev.project(string):
        OBS project name

    ev.package(string):
        Package name

    ev.repository(string):
        OBS project repository

    ev.arch(string):
        Architecture

    ts_urls(list):
        Optional list of urls of ts-devel rpms

:term:`Workitem` fields OUT

:Returns:
    result(boolean):
        True if everything is OK, False otherwise
"""

import os
import shutil
import requests
import json
import io

from tempfile import mkdtemp
from subprocess import check_call, check_output, CalledProcessError

from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.rpm import extract_rpm

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined in SkyNET API."""

    def __init__(self):
        """Initializator."""

        BuildServiceParticipant.__init__(self)
        self.gitconf = None
        self.l10n_conf = None

    def handle_wi_control(self, ctrl):
        """Control job thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Control participant thread."""

        if ctrl.message == "start":
            self.gitconf = {
                "basedir":  ctrl.config.get("git", "basedir"),
                "username": ctrl.config.get("git", "username"),
                "password": ctrl.config.get("git", "password"),
                "apiurl":   ctrl.config.get("git", "apiurl"),
                "repourl":  ctrl.config.get("git", "repourl"),
                "vcs_msg_prefix":   ctrl.config.get("git", "vcs_msg_prefix"),
            }

            self.l10n_conf = {
                "username": ctrl.config.get("l10n", "username"),
                "password": ctrl.config.get("l10n", "password"),
                "apiurl":   ctrl.config.get("l10n", "apiurl"),
            }

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Handle workitem."""

        wid.result = False

        if wid.params.ts_urls:
            self.get_ts_urls(wid.params.ts_urls)
        if wid.fields.ts_urls:
            self.get_ts_urls(wid.fields.ts_urls)
        if wid.fields.ev.package:
            self.get_ts_obs(wid)

        wid.result = True

    def get_ts_urls(self, urls):
        """Fetch -ts-devel rpms from urls"""

        for url in urls:
            tmpdir = mkdtemp()
            tsrpm = os.path.join(tmpdir, os.path.basename(url))
            if not "-ts-devel-" in tsrpm:
                continue
            fstream = requests.get(url, verify=False, stream=True)
            with io.FileIO(tsrpm, mode='wb') as fil:
                for chunk in fstream.iter_content(chunk_size=1024000):
                    fil.write(chunk)

            packagename, version = os.path.basename(tsrpm).split("-ts-devel-")
            version = version.split("-")[0]
            self.update_ts([tsrpm], packagename, version, tmpdir)
            shutil.rmtree(tmpdir)

    def get_ts_obs(self, wid):
        """Fetch -ts-devel rpms from obs to tmpdir"""

        tmpdir = mkdtemp()
        targetrepo = "%s/%s" % (wid.fields.ev.repository, wid.fields.ev.arch)
        if (wid.fields.exclude_repos
            and wid.fields.ev.repository in wid.fields.exclude_repos):
            print "Skipping excluded target %s" % targetrepo
            return []

        if (wid.fields.exclude_archs 
            and wid.fields.ev.arch in wid.fields.exclude_archs):
            print "Skipping excluded target %s" % targetrepo
            return []

        obsproject = wid.fields.ev.project
        packagename = wid.fields.ev.package
        bins = self.get_binary_list(obsproject, packagename, targetrepo)
        version = wid.fields.ev.versrel.split("-")[0]

        tsrpms = []

        for tsbin in [pkg for pkg in bins if "-ts-devel-" in pkg]:
            self.download_binary(obsproject, packagename, targetrepo,
                                 tsbin, tmpdir)
            tsrpms.append(os.path.join(tmpdir, tsbin))

        self.update_ts(tsrpms, packagename, version, tmpdir)
        shutil.rmtree(tmpdir)

    def update_ts(self, tsrpms, packagename, version, tmpdir):
        """Extract ts files from RPM and put them in GIT."""

        workdir = os.path.join(tmpdir, packagename)
        os.mkdir(workdir)

        tsfiles = []
        for tsbin in tsrpms:
            tsfiles.extend(extract_rpm(tsbin, workdir, "*.ts"))

        if len(tsfiles) == 0:
            print "No ts files in '%s'. Continue..." % packagename
            return

        try:
            projectdir = self.init_gitdir(packagename)
        except CalledProcessError:
            # invalidate cache and try once again
            self.log.warning("Caught a git error. Removing local git repo and trying again...")
            shutil.rmtree(os.path.join(self.gitconf["basedir"], packagename),
                          ignore_errors=True)
            projectdir = self.init_gitdir(packagename)

        tpldir = os.path.join(projectdir, "templates")
        if not os.path.isdir(tpldir):
            os.mkdir(tpldir)

        for tsfile in tsfiles:
            shutil.copy(os.path.join(workdir, tsfile), tpldir)

        check_call(["git", "add", "*"], cwd=tpldir)

        if len(check_output(["git", "diff", "--staged"],
                            cwd=projectdir)) == 0:
            print "No updates. Exiting"
            return

        check_call(["git", "commit", "-m",
                    "%s translation templates update for %s" % ( self.gitconf['vcs_msg_prefix'], version)],
                   cwd=projectdir)
        check_call(["git", "push", "origin", "master"], cwd=projectdir)

        # auto-create/update Pootle translation projects
        l10n_auth = (self.l10n_conf["username"], self.l10n_conf["password"])
        data = json.dumps({"name": packagename})
        resp = requests.post("%s/packages" % self.l10n_conf["apiurl"],
                             auth=l10n_auth,
                             headers={'content-type': 'application/json'},
                             data=data,
                             verify=False)
        assert resp.status_code == 201
        # This is a hack to make Pootle recalculate statistics
        resp = requests.post("%s/packages" % self.l10n_conf["apiurl"],
                             auth=l10n_auth,
                             headers={'content-type': 'application/json'},
                             data=data,
                             verify=False)
        assert resp.status_code == 201

    def init_gitdir(self, reponame):
        """Initialize local clone of remote Git repository."""

        gitdir = os.path.join(self.gitconf["basedir"], reponame)
        if reponame not in os.listdir(self.gitconf["basedir"]):
            # check if repo exists on git server
            gitserv_auth = (self.gitconf["username"], self.gitconf["password"])
            ghresp = requests.get("%s/user/repos" % self.gitconf["apiurl"],
                                  auth=gitserv_auth, verify=False)
            if reponame not in [repo['name'] for repo in ghresp.json()]:
                payload = {
                    'name': reponame,
                    'has_issues': False,
                    'has_wiki': False,
                    'has_downloads': False,
                    'auto_init': True
                }
                ghresp = requests.post("%s/user/repos" % self.gitconf["apiurl"],
                                       auth=gitserv_auth,
                                       headers={
                                           'content-type': 'application/json'
                                       },
                                       verify=False,
                                       data=json.dumps(payload))
                assert ghresp.status_code == 201

            check_call(["git", "clone",
                        self.gitconf["repourl"] % {
                            "username": self.gitconf["username"],
                            "reponame": reponame
                        }],
                       cwd=self.gitconf["basedir"])
        else:
            check_call(["git", "fetch"], cwd=gitdir)
            check_call(["git", "rebase", "origin/master"], cwd=gitdir)
        return gitdir
