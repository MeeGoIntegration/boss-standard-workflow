"""
This participant is used to extract documentation files from -doc binary RPMs
and deploy them to be served by an HTTP server.

:term:`Workitem` params IN

:Parameters:
    doc_urls(list):
        Optional list of urls of -doc rpms

    symlink:
        Name of a symlink to be created or updated to point at the deployed
        version of documentation (example: dev or stable)

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

    doc_urls(list):
        Optional list of urls of -doc rpms

:term:`Workitem` fields OUT

:Returns:
    result(boolean):
        True if everything is OK, False otherwise
"""

import os
import shutil
import requests
import io

from tempfile import mkdtemp

from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.rpm import extract_rpm

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined in SkyNET API."""

    def __init__(self):
        """Initializator."""

        BuildServiceParticipant.__init__(self)
        self.autodoc_conf = None

    def handle_wi_control(self, ctrl):
        """Control job thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Control participant thread."""

        if ctrl.message == "start":
            self.autodoc_conf = {
                "docroot": ctrl.config.get("autodoc", "docroot"),
            }

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Handle workitem."""

        wid.result = False

        if wid.params.doc_urls or wid.fields.doc_urls:
            self.get_doc_urls(wid)
        if wid.fields.ev.package:
            self.get_doc_obs(wid)

        wid.result = True

    def get_doc_urls(self, wid):
        """Fetch -doc rpms from urls"""

        urls = []
        if wid.params.doc_urls:
            urls = wid.params.doc_urls
        if wid.fields.doc_urls:
            urls.extend(wid.fields.doc_urls)

        for url in urls:
            tmpdir = mkdtemp()
            docrpm = os.path.join(tmpdir, os.path.basename(url))
            if not "-doc-" in docrpm:
                continue
            fstream = requests.get(url, verify=False, stream=True)
            with io.FileIO(docrpm, mode='wb') as fil:
                for chunk in fstream.iter_content(chunk_size=1024000):
                    fil.write(chunk)

            packagename, version = os.path.basename(docrpm).split("-doc-")
            version = version.split("-")[0]
            self.deploy_doc([docrpm], packagename, version, tmpdir, wid.params.symlink)
            shutil.rmtree(tmpdir)

    def get_doc_obs(self, wid):
        """Fetch -doc rpms from obs to tmpdir"""
        print "Start"
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
        print "getting binary list %s %s %s" % (obsproject , packagename, targetrepo)
        bins = self.get_binary_list(obsproject, packagename, targetrepo)
        print bins
        version = wid.fields.ev.versrel.split("-")[0]

        docrpms = []

        for docbin in [pkg for pkg in bins if "-doc" in pkg]:
            print "downloading %s" % docbin
            self.download_binary(obsproject, packagename, targetrepo,
                                 docbin, tmpdir)
            docrpms.append(os.path.join(tmpdir, docbin))
        print docrpms
        self.deploy_doc(docrpms, packagename, version, tmpdir, wid.params.symlink)
        shutil.rmtree(tmpdir)

    def deploy_doc(self, docrpms, packagename, version, tmpdir, symlink=None):
        """Extract doc files from RPM and put them under docroot."""

        deploydir = os.path.join(self.autodoc_conf['docroot'], packagename, version)
        print deploydir
        workdir = os.path.join(tmpdir, packagename)
        os.mkdir(workdir)

        deployed = False
        for docbin in docrpms:
            if len(docrpms) > 1:
                deploydir = os.path.join(deploydir, os.path.basename(docbin))
            print "extracting %s" % docbin
            docfiles = extract_rpm(docbin, workdir)

            toplevels = set()
            print "walking %s" % workdir
            for dirpath, dirnames, filenames in os.walk(workdir):
                for fil in filenames:
                    if fil.endswith(".html"):
                        toplevels.add(dirpath)
                        # don't look further down
                        del dirnames[:]
                        # no need to look at other files
                        break

            if len(toplevels) > 1:
                deployed = True
                for level in toplevels:
                    target = os.path.join(deploydir, os.path.basename(level))
                    shutil.rmtree(target, True)
                    shutil.copytree(level, target)

            elif len(toplevels) == 1:
                deployed = True
                print deploydir
                shutil.rmtree(deploydir, True)
                shutil.copytree(toplevels.pop(), deploydir)


        if deployed:
            # fix permissions due to cpio not honoring umask
            for root, dirs, files in os.walk(os.path.join(self.autodoc_conf['docroot'], packagename)):
                for d in dirs:  
                    os.chmod(os.path.join(root, d), 0755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0644)

            if symlink:
                symlink_name = os.path.join(self.autodoc_conf['docroot'], packagename, symlink)
                print "creating symlink %s" % symlink_name
                if os.path.lexists(symlink_name):
                    os.unlink(symlink_name)
                os.symlink(version, symlink_name)
