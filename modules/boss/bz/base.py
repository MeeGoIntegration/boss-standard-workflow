"""Basic bugzilla interface components."""

from abc import ABCMeta, abstractmethod


class BugzillaError(Exception):
    """Class presenting bugzilla errors."""
    def __init__(self, code, msg):
        super(BugzillaError, self).__init__(code, msg)
        self.code = code
        self.message = msg

    def __str__(self):
        return "[%s] %s" % (self.code or "N/A", self.message or "Unknown error")


class BaseBugzilla(object, metaclass=ABCMeta):
    """Base class for different bugzilla interfaces."""

    def __init__(self):
        self.supported_fields = {}

    @abstractmethod
    def login(self):
        """Login to Bugzilla."""
        pass

    def logout(self):
        """Logout of Bugzilla."""
        pass

    @abstractmethod
    def bug_get(self, bug_id):
        """Gets information about particular bugs in bugzilla.

        :param bug_id: Bug ID as a string
        :returns: Dictionary containing bug info
        """
        pass

    @abstractmethod
    def bug_update(self, bug_data):
        """Updates bug information with the given fields.

        :bug_data: Dictionary of bug information
        """
        pass

    @abstractmethod
    def comment_add(self, bug_id, comment, is_private):
        """Add comment to bug.

        :param bug_id: Bug ID as a string
        :param comment: Comment content
        :param is_private: Is the comment private
        """
        pass
