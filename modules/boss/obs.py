"""Helper classes for participants which deal with OBS."""
from urllib2 import HTTPError
from buildservice import BuildService

class OBSError(Exception):
    """Exception identifying OBS errors."""
    pass

class BuildServiceMixin(object):
    """Participant Mixin class for general BuildService setup."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=W0613
        self.__obs = None
        self.__obs_alias = None
        self.__oscrc = None

    def handle_lifecycle_control(self, ctrl):
        """Get OBS config"""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.__oscrc = ctrl.config.get("obs", "oscrc")
            else:
                raise RuntimeError("Missing configuration value: [obs] oscrc")

    def handle_wi(self, wid):
        """Get the namespace from workitem"""
        if not (wid.fields.ev and wid.fields.ev.namespace):
            raise RuntimeError("Mandatory field ev.namespace missing")
        if wid.fields.ev.namespace != self.__obs_alias:
            self.__obs_alias = wid.fields.ev.namespace
            self.__obs = None

    @property
    def obs(self):
        """Lazy BuildService property."""
        if self.__obs is None:
            self.__obs = BuildService(
                    oscrc=self.__oscrc,
                    apiurl=self.__obs_alias)
        return self.__obs


class RepositoryMixin(object):
    """Participant Mixin class for resolving repositories."""
    def __init__(self, *args, **kwargs):
        # pylint: disable=W0613
        if not isinstance(self, BuildServiceMixin):
            raise RuntimeError("RepositoryMixin requires BuildServiceMixin")

    def __get_repositories(self, wid, action, prefix):
        """Generic method to fetch either source or target repos."""
        project = action.get(prefix + "project", None)
        if not project:
            return None
        # Check if repos already in workitem
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
            try:
                result[repo] = self.obs.getRepositoryArchs(project, repo)
            except HTTPError, exobj:
                raise OBSError("getRepositoryArchs(%s, %s) failed: %s" %
                    (project, repo, exobj))
        setattr(wid.fields.repositories, project, result)

    def get_target_repos(self, wid, action):
        """Get target repositories for action.

        :param wid: Workitem
        :param action: OBS request action dictionary
        :retruns: {"repositoryname": ["architecture",...], ...}

        Retruns dictionary of repositories with list of architectures for the
        target project of given action.
        """
        return self.__get_repositories(wid, action, "target")

    def get_source_repos(self, wid, action):
        """Get source repositories for action.

        :param wid: Workitem
        :param action: OBS request action dictionary
        :retruns: {"repositoryname": ["architecture",...], ...}

        Retruns dictionary of repositories with list of architectures for the
        source project of given action.
        """
        return self.__get_repositories(wid, action, "source")
