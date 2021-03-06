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

    ts_branch(string):
        Optional branch to push the updates into

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
        branch = wid.fields.ts_branch

        if wid.params.ts_urls:
            self.get_ts_urls(wid.params.ts_urls, branch)
        if wid.fields.ts_urls:
            self.get_ts_urls(wid.fields.ts_urls, branch)
        if wid.fields.ev.package:
            self.get_ts_obs(wid, branch)

        wid.result = True

    def get_ts_urls(self, urls, branch):
        """Fetch -ts-devel rpms from urls"""

        for url in urls:
            tmpdir = mkdtemp()
            tsrpm = os.path.join(tmpdir, os.path.basename(url))
            if not "-ts-devel-" in tsrpm:
                continue
            fstream = requests.get(url, stream=True)
            with io.FileIO(tsrpm, mode='wb') as fil:
                for chunk in fstream.iter_content(chunk_size=1024000):
                    fil.write(chunk)

            packagename, version = os.path.basename(tsrpm).split("-ts-devel-")
            version = version.split("-")[0]
            self.update_ts([tsrpm], packagename, version, tmpdir, branch)
            shutil.rmtree(tmpdir)

    def get_ts_obs(self, wid, branch):
        """Fetch -ts-devel rpms from obs to tmpdir"""

        tmpdir = mkdtemp()
        targetrepo = "%s/%s" % (wid.fields.ev.repository, wid.fields.ev.arch)
        if (wid.fields.exclude_repos
            and wid.fields.ev.repository in wid.fields.exclude_repos):
            self.log.info("Skipping excluded target %s" % targetrepo)
            return []

        if (wid.fields.exclude_archs 
            and wid.fields.ev.arch in wid.fields.exclude_archs):
            self.log.info("Skipping excluded target %s" % targetrepo)
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
        if tsrpms:
            self.update_ts(tsrpms, packagename, version, tmpdir, branch)
        else:
            self.log.info("No -ts-devel rpms in '%s'" % packagename)
        shutil.rmtree(tmpdir)

    def update_ts(self, tsrpms, packagename, version, tmpdir, branch):
        """Extract ts files from RPM and put them in GIT."""

        workdir = os.path.join(tmpdir, packagename)
        os.mkdir(workdir)

        tsfiles = []
        for tsbin in tsrpms:
            tsfiles.extend(extract_rpm(tsbin, workdir, "*.ts"))

        if len(tsfiles) == 0:
            self.log.info("No ts files in '%s'. Continue..." % packagename)
            return

        if not branch:
            branch = "master"
        if branch != "master":
            projectname = "%s__%s__" % (packagename, branch)
        else:
            projectname = packagename
        projectdir = os.path.join(self.gitconf["basedir"], projectname)

        try:
            self.init_gitdir(projectdir, packagename, branch)
        except CalledProcessError:
            # invalidate cache and try once again
            self.log.warning(
                "Caught a git error. Removing local git repo and trying again"
            )
            shutil.rmtree(projectdir, ignore_errors=True)
            self.init_gitdir(projectdir, packagename, branch)

        tpldir = os.path.join(projectdir, "templates")
        if not os.path.isdir(tpldir):
            os.mkdir(tpldir)

        for tsfile in tsfiles:
            shutil.copy(os.path.join(workdir, tsfile), tpldir)

        check_call(["git", "add", "*"], cwd=tpldir)

        if len(check_output(["git", "diff", "--staged"],
                            cwd=projectdir)) == 0:
            self.log.info("No updates. Exiting")
            return

        commit_msg = "%s translation templates update for %s" % (
            self.gitconf['vcs_msg_prefix'], version)
        check_call(["git", "commit", "-m", commit_msg], cwd=projectdir)
        check_call(["git", "push", "origin", branch], cwd=projectdir)

        # auto-create/update Pootle translation projects
        l10n_auth = (self.l10n_conf["username"], self.l10n_conf["password"])
        data = json.dumps({"name": projectname})
        update_url = "%s/packages" % self.l10n_conf["apiurl"]
        resp = requests.post(
            update_url,
            auth=l10n_auth,
            headers={'content-type': 'application/json'},
            data=data,
        )
        resp.raise_for_status()
        try:
            # This is a hack to make Pootle recalculate statistics
            resp = requests.post(
                update_url,
                auth=l10n_auth,
                headers={'content-type': 'application/json'},
                data=data,
            )
            resp.raise_for_status()
        except requests.HTTPError:
            self.log.exception('Pootle statistic recalculation call failed')

    def init_gitdir(self, gitdir, reponame, branch):
        """Initialize local clone of remote Git repository."""
        remote_branch = "origin/%s" % branch

        if os.path.exists(gitdir):
            # The git dir is named like repository__branch__
            # so if the directory exists, we can assume the init has been done
            # already and the branch exists etc, and reseting to the remote
            # head is enough
            check_call(["git", "fetch"], cwd=gitdir)
            check_call(["git", "reset", "--hard", remote_branch], cwd=gitdir)
            return

        # check if repo exists on git server
        gitserv_auth = (self.gitconf["username"], self.gitconf["password"])
        ghresp = requests.get(
            "%s/user/repos" % self.gitconf["apiurl"], auth=gitserv_auth
        )
        if reponame not in [repo['name'] for repo in ghresp.json()]:
            # Create remote repository if it does not exist
            payload = {
                'name': reponame,
                'has_issues': False,
                'has_wiki': False,
                'has_downloads': False,
                'auto_init': True
            }
            ghresp = requests.post(
                "%s/user/repos" % self.gitconf["apiurl"],
                auth=gitserv_auth,
                headers={'content-type': 'application/json'},
                data=json.dumps(payload),
            )
            ghresp.raise_for_status()

        repo_url = self.gitconf["repourl"] % {
            "username": self.gitconf["username"],
            "reponame": reponame
        }
        # Clone the repository to the target gitdir
        check_call(["git", "clone", repo_url, gitdir],
                   cwd=self.gitconf["basedir"])
        current_branch = check_output(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=gitdir
        ).strip()
        if current_branch != branch:
            # If remote default head was not the branch we want...
            remote_branches = [
                line.strip() for line in
                check_output(
                    ["git", "branch", "--list", "--remote"], cwd=gitdir,
                ).splitlines()
            ]
            if remote_branch in remote_branches:
                # ... we checkout the branch from remote if it exists ...
                check_call(
                    ["git", "checkout", "--force", "--track", remote_branch],
                    cwd=gitdir
                )
            else:
                # ... or create a new one if it doesn't ...
                check_call(
                    ["git", "checkout", "--force", "-b", branch],
                    cwd=gitdir
                )
