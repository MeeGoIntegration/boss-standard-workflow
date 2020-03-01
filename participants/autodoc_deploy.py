"""
This participant is used to extract documentation files from -doc binary RPMs
and deploy them to be served by an HTTP server.

:term:`Workitem` params IN

:Parameters:
    doc_urls(list):
        Optional list of urls of -doc rpms

    symlink:
        Name of a symlink to be created or updated to point at the deployed
        version of documentation (example: latest)

    prefix:
        Name of a prefix directory to created

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

import io
import os
import shutil
import stat
from contextlib import contextmanager
from tempfile import mkdtemp

import requests
from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.rpm import extract_rpm


@contextmanager
def tempdir(*args, **kwargs):
    """Context manager to ensure temp dir gets removed.
    Takes same arguments as mkdtemp

    In python3 we can use tempfile.TemporaryDirectory
    """
    path = mkdtemp(*args, **kwargs)
    try:
        yield path
    finally:
        shutil.rmtree(path)


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
            with tempdir(prefix='autodoc') as tmpdir:
                docrpm = os.path.join(tmpdir, os.path.basename(url))
                if "-doc-" not in docrpm:
                    continue
                fstream = requests.get(url, verify=False, stream=True)
                with io.FileIO(docrpm, mode='wb') as fil:
                    for chunk in fstream.iter_content(chunk_size=1024000):
                        fil.write(chunk)

                packagename, version = os.path.basename(docrpm).split("-doc-")
                self.deploy_doc(
                    [docrpm], packagename, version, tmpdir,
                    wid.params.symlink, wid.params.prefix
                )

    def get_doc_obs(self, wid):
        """Fetch -doc rpms from obs to tmpdir"""
        self.log.info("Fetching from OBS...")
        with tempdir(prefix='autodoc') as tmpdir:
            targetrepo = "%s/%s" % (
                wid.fields.ev.repository, wid.fields.ev.arch
            )
            if (
                wid.fields.exclude_repos
                and wid.fields.ev.repository in wid.fields.exclude_repos
            ):
                self.log.info("Skipping excluded target %s", targetrepo)
                return []

            if (
                wid.fields.exclude_archs
                and wid.fields.ev.arch in wid.fields.exclude_archs
            ):
                self.log.info("Skipping excluded target %s", targetrepo)
                return []

            obsproject = wid.fields.ev.project
            packagename = wid.fields.ev.package
            self.log.debug(
                "Getting binary list %s %s %s",
                obsproject, packagename, targetrepo
            )
            bins = self.get_binary_list(obsproject, packagename, targetrepo)
            self.log.debug("Got bins: %s", bins)
            version = ".".join([
                wid.fields.ev.versrel.rsplit("-", 1)[0], wid.fields.ev.bcnt
            ])

            docrpms = []
            doc_package_names = [
                pkg for pkg in bins
                if ("-doc" in pkg and not pkg.endswith("src.rpm"))
            ]
            for docbin in doc_package_names:
                self.log.debug("downloading %s", docbin)
                self.download_binary(
                    obsproject, packagename, targetrepo, docbin, tmpdir
                )
                docrpms.append(os.path.join(tmpdir, docbin))
            self.log.debug("Downloaded files: %", docrpms)
            self.deploy_doc(
                docrpms, packagename, version, tmpdir,
                wid.params.symlink, wid.params.prefix
            )

    def deploy_doc(
        self, docrpms, packagename, version, tmpdir,
        symlink=None, prefix=None
    ):
        """Extract -doc- files from RPM and put them under docroot."""

        deploydir = version
        if prefix:
            deploydir = os.path.join(prefix, version)
        deploydir = os.path.join(
            self.autodoc_conf['docroot'], packagename, deploydir)
        self.log.info("Depolying to %s", deploydir)
        workdir = os.path.join(tmpdir, packagename)
        os.mkdir(workdir)

        deployed = False
        for docbin in docrpms:
            if len(docrpms) > 1:
                deploydir = os.path.join(deploydir, os.path.basename(docbin))
            self.log.debug("Extracting %s", docbin)
            extract_rpm(docbin, workdir)

            toplevels = set()
            self.log.debug("Walking %s", workdir)
            for dirpath, dirnames, filenames in os.walk(workdir):
                for fil in filenames:
                    if fil.endswith(".html") or fil:
                        toplevels.add(dirpath)
                        # don't look further down
                        del dirnames[:]
                        # no need to look at other files
                        break

            if len(toplevels) > 1:
                deployed = True
                for level in toplevels:
                    target = os.path.join(deploydir, os.path.basename(level))
                    self.log.debug("Removing %s", target)
                    shutil.rmtree(target, True)
                    shutil.copytree(level, target)
            elif len(toplevels) == 1:
                deployed = True
                self.log.debug("Removing %s", deploydir)
                shutil.rmtree(deploydir, True)
                shutil.copytree(toplevels.pop(), deploydir)

        if deployed:
            self.log.info("Stuff was deployed")
            # fix permissions due to cpio no honoring umask
            dirmode = (stat.S_IRWXU |
                       stat.S_IRGRP | stat.S_IXGRP |
                       stat.S_IROTH | stat.S_IXOTH)
            filemode = (stat.S_IRUSR | stat.S_IWUSR |
                        stat.S_IRGRP | stat.S_IROTH)
            package_path = os.path.join(
                self.autodoc_conf['docroot'], packagename)
            for root, dirs, files in os.walk(package_path):
                for d in dirs:
                    self.log.debug("fixing permission for %s", d)
                    os.chmod(os.path.join(root, d), dirmode)
                for f in files:
                    os.chmod(os.path.join(root, f), filemode)

            if symlink:
                symlink_name = symlink
                if prefix:
                    symlink_name = os.path.join(prefix, symlink)
                symlink_name = os.path.join(
                    self.autodoc_conf['docroot'], packagename, symlink_name)
                self.log.debug("Creating symlink %s", symlink_name)
                if os.path.lexists(symlink_name):
                    os.unlink(symlink_name)
                os.symlink(deploydir, symlink_name)
                with open("%s.id" % symlink_name, 'w') as symid:
                    symid.write(version)
