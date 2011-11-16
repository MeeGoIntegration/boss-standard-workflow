"""Helper classes for participants which deal with OBS."""

import os
from functools import wraps
from urllib2 import HTTPError

from buildservice import BuildService


class OBSError(Exception):
    """Exception identifying OBS errors."""
    pass

class BuildServiceParticipant(object):
    """Base class for participants using BuildService.

    Automates the BuildService setup with decorators for participant
    handle_lifecycle_control() and handle_wi().

    Example::

        class ParticipantHandler(BuildServiceParticipant):

            @BuildServiceParticipant.get_oscrc
            def handle_lifecycle_control(self, ctrl):
                # Decorator gets the required osc config from control message at
                # start
                pass

            @BuildServiceParticipant.setup_obs
            def handle_wi(self, wid):
                # Decorator instantiates the BbuildService based on ev.namespace
                # field provided in workitem. BuildService is available as
                # property self.obs

                ...

    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=W0613
        self.__obs_mocked = False
        self.__obs = None
        self.__obs_alias = None
        self.__oscrc = None

    @classmethod
    def get_oscrc(cls, method):
        """Decorator for getting [obs] oscrc from participant configuration.

        Can be used on participant handle_lifecycle_control() method.
        """
        @wraps(method)
        def wrapper(self, ctrl):
            # pylint: disable=C0111
            if not isinstance(self, cls):
                raise RuntimeError("get_oscrc decoarator can only be used for "
                    "methods of %s subclasses" % cls.__name__)

            if ctrl.message == "start":
                if ctrl.config.has_option("obs", "oscrc"):
                    self.__oscrc = ctrl.config.get("obs", "oscrc")
                else:
                    raise RuntimeError("Missing configuration value: "
                            "[obs] oscrc")
            return method(self, ctrl)
        return wrapper

    @classmethod
    def setup_obs(cls, method):
        """Decorator to get the namespace from workitem.

        Can be used on participant handle_wi() method.
        """
        @wraps(method)
        def wrapper(self, wid):
            # pylint: disable=C0111,W0212
            if not isinstance(self, cls):
                raise RuntimeError("setup_obs decoarator can only be used for "
                    "methods of %s subclasses" % cls.__name__)

            if not (wid.fields.ev and wid.fields.ev.namespace):
                raise RuntimeError("Mandatory field ev.namespace missing")
            if wid.fields.ev.namespace != self.__obs_alias:
                self.__obs_alias = wid.fields.ev.namespace
                if not self.__obs_mocked:
                    self.__obs = None
            return method(self, wid)
        return wrapper

    def __get_obs(self):
        """Lazy BuildService property."""
        if self.__obs is None:
            if self.__oscrc is None or self.__obs_alias is None:
                raise RuntimeError("BuildService conf values not set. "
                        "Use get_oscrc and setup_obs decorators.")
            self.__obs = BuildService(
                    oscrc=self.__oscrc,
                    apiurl=self.__obs_alias)
        return self.__obs

    def __set_obs(self, instance):
        """Setter needed for mocking BuildService in unit tests."""
        # Make an exception for mock objects used in unit testing
        if not hasattr(instance, "reset_mock"):
            raise AttributeError("obs is read only property")
        self.__obs_mocked = True
        self.__obs = instance

    obs = property(__get_obs, __set_obs)


class RepositoryMixin(object):
    """Participant Mixin class for fetching repository information from OBS.

    Provided methods require BuildService as member {{{obs}}}, so using
    BuildServiceParticipant is recommended.

    Example::

        class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):

            @BuildServiceParticipant.get_oscrc
            def handle_lifecycle_control(self, ctrl):
                pass

            @BuildServiceParticipant.setup_obs
            def handle_wi(self, wid):
                repos = self.get_project_repos("someproject")
                # Do something with the repository info

                ...

    """

    def get_project_repos(self, project, wid=None):
        """Get project repository information.

        :param project: Project name
        :param wid: Workitem used to cache repository info
            * If None, no caching is used
        :returns: Dictionary containing the repository information

        If workitem is not given or it does not contain the repository
        information for requested project, then the information is fetched from
        OBS.

        Returned dictionary has the following format::

            {
                "repository_name": {
                    "path": path of this repository,
                    "targets": paths of the repositories this repository builds
                               against
                    "architectures": list of architectures for this repository
                    },
                ...
            }

        """
        # Check if repos already in workitem
        if wid is not None:
            if wid.fields.repositories is not None:
                result = getattr(wid.fields.repositories, project, None)
                if result is not None:
                    return result.as_dict()
            else:
                wid.fields.repositories = {}

        # Fetch repositories from OBS
        result = {}
        try:
            repositories = self.obs.getProjectRepositories(project)
        except HTTPError, exobj:
            if exobj.code == 404:
                msg = "project not found"
            else:
                msg = str(exobj)
            raise OBSError("getProjectRepositories(%s) failed: %s" %
                    (project, msg))

        for repo in repositories:
            result[repo] = {"path": "%s/%s" % (project, repo)}
            try:
                result[repo]["architectures"] = self.obs.getRepositoryArchs(
                        project, repo)
            except HTTPError, exobj:
                raise OBSError("getRepositoryArchs(%s, %s) failed: %s" %
                    (project, repo, exobj))
            try:
                result[repo]["targets"] = self.obs.getRepositoryTargets(
                        project, repo)
            except HTTPError, exobj:
                raise OBSError("getRepositoryTargets(%s, %s) failed: %s" %
                    (project, repo, exobj))
            if not len(result[repo]["architectures"]):
                del(result[repo])
        if wid is not None:
            setattr(wid.fields.repositories, project, result)
        return result

    def get_target_repos(self, action, wid=None):
        """Get target project repositories for action.

        :param action: OBS request action dictionary
        :param wid: Workitem used to cache repository info
            * If None, no caching is used
        :retruns: Repository info with same format as get_project_repos()
        """
        project = action.get("targetproject", None)
        if not project:
            raise RuntimeError("targetproject not defined in action")
        return self.get_project_repos(project, wid)

    def get_source_repos(self, action, wid=None):
        """Get source repositories for action.

        :param action: OBS request action dictionary
        :param wid: Workitem used to cache repository info
            * If None, no caching is used
        :retruns: Repository info with same format as get_project_repos()
        """
        project = action.get("sourceproject", None)
        if not project:
            raise RuntimeError("sourceproject not defined in action")
        return self.get_project_repos(project, wid)

    def get_project_targets(self, project, wid=None):
        """Get list of repository targets for project.

        :param project: OBS Project name
        :returns: List of targest in format "repository_name/architecture"
        """
        targets = []
        repositories = self.get_project_repos(project, wid=wid)
        for repo, info in repositories.iteritems():
            for arch in info["architectures"]:
                targets.append("%s/%s" % (repo, arch))
        return targets

    def get_binary_list(self, project, package, target):
        """Get binary list from OBS repository.

        :param project: Project name
        :param package: Package name
        :param target: Build target e.g. "repository/arch"
        :returns: List of built filenames

        NOTE: Returned list includes src.rpm
        """
        try:
            bin_list = self.obs.getBinaryList(project, target, package)
        except HTTPError, exobj:
            raise OBSError("getBinaryList(%s, %s, %s) failed: %s" %
                    (project, target, package, exobj))
        return bin_list

    def download_binary(self, project, package, target, binary, path):
        """Download binary from OBS.

        :param project: Project name
        :param package: Package name
        :param target: Build target e.g. "repository/arch"
        :param binary: Binary file name
        :param path: Directory path for download to
        :raises ValueError: if <path> does not exists, is not directory or is
                not writable
        :raises OBSError: If downloading fails
        :returns: Absolute path to downloaded file

        File will be downloaded to <path>/<binary>, if file already exists it
        will be overwriten.

        """
        path = os.path.abspath(path)
        if not os.access(path, os.W_OK):
            raise ValueError("Path '%s' does not exist or not writable" % path)
        if not os.path.isdir(path):
            raise ValueError("Path '%s' is not directory" % path)
        path = os.path.join(path, binary)
        try:
            self.obs.getBinary(project, target, package, binary, path)
        except HTTPError, exobj:
            if exobj.code == 404:
                msg = "Binary '%s' not found for %s %s %s" % \
                        (binary, project, package, target)
            else:
                msg = "Failed to download binary '%s' from %s %s %s: %s" % \
                        (binary, project, package, target, exobj)
            raise OBSError(msg)
        except Exception, exobj:
            raise OBSError("Failed to download binary '%s' from %s %s %s: %s" %
                    (binary, project, package, target, exobj))
        return path
