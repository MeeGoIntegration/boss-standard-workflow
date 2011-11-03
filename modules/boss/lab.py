"""This module provides utilities to work with temporary files."""

import difflib, os, shutil, tempfile, re

class Lab(object):
    """Controlled temporary directory with snapshot support.

    Can be used with 'with' statement to create disposable file storage.
    Does not support subdirectories.
    """

    __parent = re.compile("(^|\/)\.\.(\/|$)")

    def __init__(self, prefix=""):
        path = tempfile.mkdtemp(prefix=prefix)
        self._history = [path]

    def _snapshot_root(self, sid):
        """Returns snapshot root path."""
        try:
            return self._history[sid]
        except IndexError:
            raise ValueError("Bad snapshot id %d" % sid)

    @property
    def path(self):
        """Root directory of the lab."""
        return self._snapshot_root(0)

    def take_snapshot(self):
        """Take snapshot of the lab directory.

        :returns: Snapshot ID
        """
        index = len(self._history)
        path = self.path + "_%d" % index
        self._history.append(path)
        shutil.copytree(self.path, path)
        return index

    def store(self, name, content):
        """Saves a file in the lab.

        :param name: File name
        :param content: File content
        """
        path = self.real_path(name)
        open(path, "w").writelines(content)

    def mkdir(self, path, mode=0777):
        """os.mkdir() equivalent except works under lab dir."""
        os.mkdir(self.real_path(path), mode)

    def makedirs(self, path, mode=0777):
        """os.makedirs() equivalent except works under lab dir."""
        os.makedirs(self.real_path(path), mode)

    def open(self, *args, **kwargs):
        """Open file.

        Takes same arguments as built in open()

        :param sid: Snapshot id. Default is current working copy

        Snapshot files can only be opened for reading
        """
        sid = kwargs.pop("sid", 0)
        if sid:
            mode = kwargs.get("mode", None) or (args + (None, None))[1]
            if mode and ("w" in mode or "a" in mode):
                raise ValueError("Snapshots are not supposed to be altered")
        if args:
            name = self.real_path(args[0], sid)
            args = (name,) + args[1:]
        elif kwargs.has_key("name"):
            kwargs["name"] = self.real_path(kwargs["name"], sid)

        return open(*args, **kwargs)

    def get_diff(self, name, from_sid, to_sid=0):
        """Compares the original file content between two snapshots

        :param name: File name
        :param from_sid: Snapshot ID to compare from
        :param to_sid: Snapshot id to compare to, default current working copy
        :returns: List of changed lines
        """
        try:
            from_lines = self.open(name, sid=from_sid).readlines()
        except IOError, exc:
            if exc.errno == 2:
                from_lines = []
            else:
                raise
        try:
            to_lines = self.open(name, sid=to_sid).readlines()
        except IOError, exc:
            if exc.errno == 2:
                to_lines = []
            else:
                raise

        diff = difflib.Differ().compare(from_lines, to_lines)
        return [line for line in diff if not line.startswith("  ")]

    def real_path(self, path, sid=0):
        """Get file path.

        :param path: File path/name
        :param sid: Snapshot id, default current
        :returns: Full path to file under lab
        """
        if self.__parent.search(path):
            raise ValueError(".. not allowed in file paths")
        return os.path.join(self._snapshot_root(sid),
                path.strip().lstrip(os.path.sep))

    def cleanup(self):
        """Cleanup the lab and snapshots."""
        for path in list(self._history):
            shutil.rmtree(path)
            self._history.remove(path)

    def __enter__(self):
        """Managed context entry point."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Managed context exit point."""
        self.cleanup()
