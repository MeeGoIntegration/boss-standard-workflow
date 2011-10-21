"""Helper classes for participants which deal with OBS."""
from functools import wraps
from urllib2 import HTTPError
from buildservice import BuildService


class OBSError(Exception):
    """Exception identifying OBS errors."""
    pass

class BuildServiceParticipant(object):
    """Participant Mixin class for general BuildService setup."""

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
            # pylint: disable=C0111
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

    @property
    def obs(self):
        """Lazy BuildService property."""
        if self.__obs is None:
            if self.__oscrc is None or self.__obs_alias is None:
                raise RuntimeError("BuildService conf values not set. "
                        "Use get_oscrc and setup_obs decorators.")
            self.__obs = BuildService(
                    oscrc=self.__oscrc,
                    apiurl=self.__obs_alias)
        return self.__obs

    @obs.setter
    def obs(self, instance):
        """Setter needed for mocking BuildService in unit tests."""
        if instance.__class__.__name__ != "Mock":
            raise AttributeError("obs is read only property")
        self.__obs_mocked = True
        self.__obs = instance


class RepositoryMixin(object):
    """Participant Mixin class for resolving repositories."""

    def __get_repositories(self, wid, action, project_id):
        """Generic method to fetch either source or target repos."""
        project = action.get(project_id, None)
        if not project:
            raise RuntimeError("%s not defined in action" % project_id)
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
        return result

    def get_target_repos(self, wid, action):
        """Get target repositories for action.

        :param wid: Workitem
        :param action: OBS request action dictionary
        :retruns: {"repositoryname": ["architecture",...], ...}

        Retruns dictionary of repositories with list of architectures for the
        target project of given action.
        """
        return self.__get_repositories(wid, action, "targetproject")

    def get_source_repos(self, wid, action):
        """Get source repositories for action.

        :param wid: Workitem
        :param action: OBS request action dictionary
        :retruns: {"repositoryname": ["architecture",...], ...}

        Retruns dictionary of repositories with list of architectures for the
        source project of given action.
        """
        return self.__get_repositories(wid, action, "sourceproject")
