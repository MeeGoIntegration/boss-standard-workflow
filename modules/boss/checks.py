"""BOSS check participant helpers."""

from functools import wraps
from RuoteAMQP.workitem import Workitem

class CheckActionProcessor(object):
    """OBS action check processing decorator.

    Used for functions or methods which check a single action (package) in
    OBS request data. Decorator takes the checks configuration from workitem
    field package_conf.<package_name>.checks and decides based on that how the
    check function should be aplied.

    <package_name> is extracted automatically from the action dictionary
    passed to the decorated function.

    Looks for value in workitem field
    package_conf.<package_name>.checks.<check_name>.

    Currently followinf values are supported:

    "skip":
        Does not execute the check on this action, logs "skipped" in
        workitem msg list.

    "warn":
        Executes the check, but if it returns False, logs a warning and
        changes the return value to True

    "quiet":
        Execute check and only log failures in workitem msg list.

    "verbose":
        (Default) Execute check and log result in workitem msg list.

    The decorated function is expected to return tuple (success, message),
    where success is True on success, False on failure, and message is the
    descriptive message about failure.

    Messages recorded in workitem msg list are of format::

        <STATUS> <check name> (<package name>): <message>

    So it is not necessary to include check or package name to the returned
    message, just description about what was wrong.

    """
    # Decorator does not need public methods
    # pylint: disable=R0903

    # supported levels
    LEVELS = ("verbose", "quiet", "warn", "skip")

    def __init__(self, check_name, action_idx=1, wid_idx=2,
            action_types=None):
        """Decorator constructor.

        :param check_name: Name of this check.
                * Identifies the check in the package checks configuration
        :param action_idx: Index of the actions dictionary in the arguments.
                * In case of integer, taken from positional arguments
                * In case of string, taken from keyword arguments
                * Default: 1 (assuming that used on a method and 0 is self)
        :param wid_idx: Index of the workitem in the arguments.
                * Similar to action_idx.
                * Default: 2
        :param action_types: List of action types supposed to be handled.
                * Default: ["submit"]
        """
        self.name = check_name
        self.action_types = action_types or ["submit"]
        self.action_idx = action_idx
        self.wid_idx = wid_idx

    def _get_action(self, args, kwargs):
        """Helper to get the action dict from arguments."""
        if isinstance(self.action_idx, int):
            action = args[self.action_idx]
        else:
            action = kwargs[self.action_idx]
        if not isinstance(action, dict):
            raise TypeError("Argument %s is supposed to be dictionary." %
                    self.action_idx)
        return action

    def _get_wid(self, args, kwargs):
        """Helper to get the workitem from arguments."""
        if isinstance(self.wid_idx, int):
            wid = args[self.wid_idx]
        else:
            wid = kwargs[self.wid_idx]
        if not isinstance(wid, Workitem):
            raise TypeError("Argument %s is supposed to be Workitem." %
                    self.wid_idx)
        return wid

    def _handle_message(self, level, package, success, message):
        """Helper to process the message based on level."""
        if not success:
            if level == "warn":
                success = True
                message = "WARNING %s (%s): %s" % \
                        (self.name, package, message)
            else:
                message = "FAILED %s (%s): %s" % \
                        (self.name, package, message)
        else:
            if level in ["warn", "verbose"]:
                message = "SUCCESS %s (%s): %s" % \
                    (self.name, package, message or "")
            elif level == "quiet":
                message = None
        return success, message

    def __call__(self, func):
        """Decorator call method.

        The decorated function must return tuple (true/false, message)
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wraps the action processor execution."""
            action = self._get_action(args, kwargs)
            wid = self._get_wid(args, kwargs)
            if not isinstance(wid.fields.msg, list):
                wid.fields.msg = []

            if action["type"] not in self.action_types:
                return (True, "Unsupported action type '%s'" % action["type"])

            package = action.get("sourcepackage", None) \
                    or action.get("targetpackage", None) \
                    or action.get("deletepackage", None)
            # If we can't resolve the package name, or there is no package_conf,
            # just execute the actual processor
            if not package:
                return func(*args, **kwargs)
            if wid.fields.package_conf is None:
                conf = {}
            else:
                conf = wid.fields.package_conf.as_dict()

            level = conf.get(package, {}).get("checks", {}).get(self.name,
                    "verbose")
            if level not in self.LEVELS:
                wid.fields.msg.append("Unknown check level '%s' for %s %s. "
                        "Should be one of %s" % (level, package, self.name,
                            self.LEVELS))
                level = "verbose"

            if level == "skip":
                success, message = (True, "SKIPPED %s (%s)" %
                        (self.name, package))
            else:
                success, message = func(*args, **kwargs)

            success, message = self._handle_message(
                    level, package, success, message)

            if message is not None:
                wid.fields.msg.append(message)
            return success, message

        return wrapper
