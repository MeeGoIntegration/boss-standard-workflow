"""Basic bugzilla interface components."""

from abc import ABCMeta, abstractmethod
from new import classobj

class BugzillaError(Exception):
    """Class presenting bugzilla errors."""
    def __init__(self, code, msg):
        super(BugzillaError, self).__init__(code, msg)
        self.code = code
        self.message = msg

    def __str__(self):
        return "[%s] %s" % (self.code or "N/A", self.message or "Unknown error")

class FieldsObject(object):
    """Container class turning dict keys into attributes."""
    def __init__(self, fields):
        self.__dict__["_data"] = fields
        self.__dict__["_changed"] = set()
        self.__dict__["_fields"] = []

    def get_changed(self):
        changed = {}
        for key in self._changed:
            changed[key] = self._data[key]
        return changed
    
    def __setattr__(self, name, value):
        if self._data[name] != value:
            self._changed.add(name)
        self._data[name] = value

    def __getattr__(self, name):
        if not self._data.has_key(name) and \
                name not in self._fields:
            raise AttributeError("Field '%s' not supported" % name)
        return self._data.get(name)

class BugAPI(FieldsObject):
    """Class presenting the Bug."""

    _api = None

    def __init__(self, fields):
        super(BugAPI, self).__init__(fields)
        self.__dict__["_fields"] = self._api.supported_fields
    
    @classmethod
    def get(cls, bug_id):
        """Get specific bug.
        :returns: Single Bug object
        """
        return cls(cls._api.bug_get(bug_id))

    def update(self):
        """Update the changes in this bug to bugzilla."""
        params = {"id": self.id}
        params.update(self.get_changed())
        self._api.bug_update(params)
        self._changed.clear()

    def add_comment(self, comment, is_private=False):
        """Add comment to this bug."""
        self._api.comment_add(self.id, comment, is_private)
        

class BaseBugzilla(object):
    """Base class for different bugzilla interfaces."""

    __metaclass__ = ABCMeta

    def __init__(self):
        self.supported_fields = {}
        self.Bug = classobj("Bug", (BugAPI,), {"_api": self})

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
