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

    Currently two values are supported:

    "skip":
        Does not execute the check on this action, logs "skipped" in
        workitem msg list.

    "warn":
        Executes the check, but if it returns False, logs a warning and
        changes the return value to True

    The decorated function is expected to return tuple (success, message),
    where success is True on success, False on failure, and message is the
    descriptive message about failure.

    Wrapper records message to workitem msg list with following format::

      <STATUS> <check_name> (<package_name>): message returned from check method

    In case of failure the message is always added to workitem msg list.
    In case of success message is not added in workitem msg list if it's None

    """
    # Decorator does not need public methods
    # pylint: disable=R0903

    def __init__(self, check_name, action_idx=1, wid_idx=2,
            action_types=None, operate_on="package"):
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
        :param operate_on: "package" or "project", TODO: separate project check
                in its own decorator
        """
        self.name = check_name
        self.action_types = action_types or ["submit"]
        self.action_idx = action_idx
        self.wid_idx = wid_idx
        if operate_on not in ["package", "project"]:
            raise ValueError("operate_on should be 'package' or 'project'")
        self.operate_on = operate_on

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

            target = action.get("source" + self.operate_on, None) \
                    or action.get("target" + self.operate_on, None) \
                    or action.get("delete" + self.operate_on, None)
            # If we can't resolve the package name, or there is no package_conf,
            # just execute the actual processor
            if not target:
                return func(*args, **kwargs)

            if self.operate_on == "package":
                if wid.fields.package_conf is None:
                    conf = {}
                else:
                    conf = wid.fields.package_conf.as_dict()
                level = conf.get(target, {}).get("checks", {}).get(self.name, None)
            else:
                # TODO: project level conf support
                level = None

            if level == "skip":
                wid.fields.msg.append("SKIPPED %s (%s)" %
                        (self.name, target))
                success, message = (True, None)
            else:
                success, message = func(*args, **kwargs)

            if not success:
                if level == "warn":
                    success = True
                    wid.fields.msg.append("WARNING %s (%s) failed: %s" %
                            (self.name, target, message))
                else:
                    wid.fields.msg.append("FAILED %s (%s): %s" %
                            (self.name, target, message))
            elif message:
                wid.fields.msg.append("INFO %s (%s): %s" %
                        (self.name, target, message))

            return success, message

        return wrapper
