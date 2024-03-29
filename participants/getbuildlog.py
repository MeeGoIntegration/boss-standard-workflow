#!/usr/bin/python
""" Gets the type and details of failure for the list of packages provided,
    and downloads the OBS build log when availalble.
    The logs are saved to a directory as configured, which might then be served
    over HTTP. Also the path to the file is appeneded to the attachments list,
    so it gets attached to a notification email.

.. warning::
    If the new_failures field does not provide the list of packages to lookup,
    then the packages field is used.
    The new_failures field is provided by the get_build_trial_results
    participant.

:term:`Workitem` fields IN

:Parameters:
    new_failures(list):
       A list of package names that have been marked as failed
    packages(list):
       used if new_failures is not provided
    test_project(string):
       the project where the failed packages live
    repository(string):
       repository in above mentioned project
    archs(list):
       list of build achitectures to look into
    ev.id(string):
       The request id being handled

:term:`Workitem` fields OUT

:Returns:
    msg(list):
       appends information about the failures to the message list
    attachments(list):
       appends the full path of the logfile to be attached to an email
    result(boolean):
       True if everything went OK, False otherwise

"""

import os
from ConfigParser import Error

from boss.obs import BuildServiceParticipant


class ParticipantHandler(BuildServiceParticipant):
    """ Class implementation as needed by SkyNet API"""

    def __init__(self):
        super(ParticipantHandler, self).__init__()
        self.logdir = None

    def handle_wi_control(self, ctrl):
        """Participant Workitem controller."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant life cycle controller."""
        if ctrl.message == "start":
            try:
                self.logdir = ctrl.config.get("getbuildlog", "logdir")
            except Error, err:
                raise RuntimeError("Participant configuration error: %s" % err)

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Workitem handler."""

        wid.result = False

        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []
        if not isinstance(wid.fields.attachments, list):
            wid.fields.attachments = []
        missing = [
            name for name in ["test_project", "repository", "archs"]
            if not getattr(wid.fields, name, None)
        ]
        if missing:
            raise RuntimeError(
                "Missing mandatory field(s): %s" % ", ".join(missing)
            )
        prj = wid.fields.test_project
        repo = wid.fields.repository
        archs = wid.fields.archs
        rid = wid.fields.ev.id
        if rid:
            pkgs = wid.fields.new_failures
        else:
            pkgs = wid.fields.packages
        if not pkgs:
            raise RuntimeError(
                "Missing mandatory field new_failures or packages"
            )

        for pkg in pkgs:
            for arch in archs:
                if not self.obs.isPackageSucceeded(prj, repo, pkg, arch):

                    pkglog = "%s-%s.log" % (pkg, arch)
                    os.mkdir(os.path.join(self.logdir, rid))
                    filename = os.path.join(self.logdir, rid, pkglog)

                    log = self.obs.getBuildLog(
                        prj, "%s/%s" % (repo, arch), pkg
                    )

                    with open(filename, 'w') as logfile:
                        logfile.write(log)

                    wid.fields.attachments.append(filename)

                    msg = "%s failed to build in %s, log attached." % (
                        pkg, prj)
                else:
                    pkg_result = self.obs.getPackageResults(
                            prj, repo, pkg, arch)
                    msg = "%s %s in %s, %s." % (
                        pkg, pkg_result['code'], prj, pkg_result['details'])

                wid.fields.msg.append(msg)

        wid.result = True
