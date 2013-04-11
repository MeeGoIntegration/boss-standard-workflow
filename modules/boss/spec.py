from __future__ import absolute_import
from tempfile import NamedTemporaryFile
import rpm

def parse_spec(spec_file):
    """Simple wrapper around rpm.spec that catches errors printed to stdout
    :param spec_file: spec file name
    :returns: rpm.spec object instance
    :raises: ValueError in case parsing failed
    """

    with NamedTemporaryFile(mode="w+") as tmplog:
        # rpm will print errors to stdout if logfile is not set
        rpm.setLogFile(tmplog)

        try:
            spec = rpm.spec(spec_file)
        except ValueError as exc:
            # re-raise errors with rpm output appended to message
            raise ValueError(str(exc) + open(tmplog.name, 'r').read())

        return spec

