"""
This participant is used to extract ts files from -ts-devel binary RPMs
and upload them to translation Git repositories.

:term:`Workitem` fields IN

:Parameters:
    ev.actions(list):
        submit request data structure :term:`actions`

:term:`Workitem` fields OUT

:Returns:
    result(boolean):
        True if everything is OK, False otherwise
"""

import os
import shutil
import requests
import json

from tempfile import mkdtemp
from subprocess import check_call, check_output

from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.rpm import extract_rpm

GIT_DIR = "/tmp/gitrepos"
GIT_USERNAME = 'rojkov'
GIT_PASSWORD = 'password'

def init_gitdir(reponame):
    """Initialize local clone of remote Git repository."""

    gitdir = os.path.join(GIT_DIR, reponame)
    if reponame not in os.listdir(GIT_DIR):
        # check if repo exists on git server
        gitserv_auth = (GIT_USERNAME, GIT_PASSWORD)
        ghresp = requests.get('https://api.github.com/user/repos',
                              auth=gitserv_auth)
        if reponame not in [repo['name'] for repo in ghresp.json]:
            payload = {
                'name': reponame,
                'has_issues': False,
                'has_wiki': False,
                'has_downloads': False,
                'auto_init': True
            }
            ghresp = requests.post('https://api.github.com/user/repos',
                                   auth=gitserv_auth,
                                   headers={'content-type': 'application/json'},
                                   data=json.dumps(payload))
            assert ghresp.status_code == 201

        check_call(["git", "clone",
                    "git@github.com:%s/%s.git" % (GIT_USERNAME, reponame)],
                   cwd=GIT_DIR)
    else:
        check_call(["git", "fetch"], cwd=gitdir)
        check_call(["git", "rebase", "origin/master"], cwd=gitdir)
    return gitdir

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined in SkyNET API."""

    def handle_wi_control(self, ctrl):
        """Control job thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Control participant thread."""

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Handle workitem."""

        wid.result = False

        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field \"ev.actions\"")

        tmpdir = mkdtemp()

        for action in wid.fields.ev.actions:
            if action["type"] != "submit":
                continue

            obsproject = action["targetproject"]
            packagename = action["targetpackage"]
            targetrepo = self.get_project_targets(obsproject, wid)[0]
            bins = self.get_binary_list(obsproject, packagename, targetrepo)

            workdir = os.path.join(tmpdir, packagename)
            os.mkdir(workdir)
            tsfiles = []
            for tsbin in [pkg for pkg in bins if "-ts-devel-" in pkg]:
                self.download_binary(obsproject, packagename, targetrepo,
                                     tsbin, tmpdir)
                tsfiles.extend(extract_rpm(os.path.join(tmpdir, tsbin),
                                           workdir, "*.ts"))
            if len(tsfiles) == 0:
                print "No ts files in '%s'. Continue..." % packagename
                continue

            projectdir = init_gitdir(packagename)

            tpldir = os.path.join(projectdir, "templates")
            if not os.path.isdir(tpldir):
                os.mkdir(tpldir)

            for tsfile in tsfiles:
                shutil.copy(os.path.join(workdir, tsfile), tpldir)

            check_call(["git", "add", "*"], cwd=tpldir)

            if len(check_output(["git", "diff", "--staged"],
                                cwd=projectdir)) == 0:
                print("No updates. Exiting")
                continue

            check_call(["git", "commit", "-m",
                        "translation templates update for some versioned tag"], #TODO: do we have version in wi?
                       cwd=projectdir)
            check_call(["git", "push", "origin", "master"], cwd=projectdir)

        shutil.rmtree(tmpdir)
        wid.result = True
