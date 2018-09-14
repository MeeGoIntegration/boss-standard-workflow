"""RPM package handling helpers."""

from __future__ import absolute_import
from subprocess import Popen, PIPE, CalledProcessError
from tempfile import NamedTemporaryFile
import rpm


def parse_spec(spec_file, keep_config=False):
    """Simple wrapper around rpm.spec that catches errors printed to stdout
    :param spec_file: spec file name
    :param keep_config: If set to True, does not call rpm.reloadConfig()
        This can be used to preserve the internal rpm state with any custom
        macros or definitions.
    :returns: rpm.spec object instance
    :raises: ValueError in case parsing failed
    """
    if not keep_config:
        rpm.reloadConfig()

    with NamedTemporaryFile(mode="w+") as tmplog:
        # rpm will print errors to stdout if logfile is not set
        rpm.setLogFile(tmplog)

        try:
            spec = rpm.spec(spec_file)
        except ValueError as exc:
            # re-raise errors with rpm output appended to message
            raise ValueError(str(exc) + open(tmplog.name, 'r').read())
        return spec


def extract_rpm(rpm_file, work_dir, patterns=None):
    """Extract rpm package contents.

    :param rpm_file: RPM file name
    :param work_dir: The RPM is extracted under this direcory.
            Also rpm filename can be given relative to this dir
    :param patterns: List of filename patterns to extract. Extract all if None
    :returns: List of extracted filenames (relative to work_dir)
    :raises: subprocess.CalledProcessError if extraction failed
    """

    tmp_patterns = None
    rpm2cpio_args = ["rpm2cpio", rpm_file]
    cpio_args = ["cpio", '-idv']
    if patterns:
        tmp_patterns = NamedTemporaryFile(mode="w")
        tmp_patterns.file.writelines([pat + "\n" for pat in patterns])
        tmp_patterns.file.flush()
        cpio_args += ["-E", tmp_patterns.name]

    p_convert = Popen(rpm2cpio_args, stdout=PIPE, cwd=work_dir)
    p_extract = Popen(cpio_args,
        stdin=p_convert.stdout, stderr=PIPE, cwd=work_dir)
    # Close our copy of the fd after p_extract forked it
    p_convert.stdout.close()

    _, std_err = p_extract.communicate()
    p_convert.wait()

    if tmp_patterns:
        tmp_patterns.close()

    if p_convert.returncode:
        raise CalledProcessError(p_convert.returncode, rpm2cpio_args)
    if p_extract.returncode:
        raise CalledProcessError(p_extract.returncode, cpio_args)

    file_list = std_err.strip().split('\n')
    # cpio reports blocks on the last line
    return [line.strip() for line in file_list[:-1] if not line.startswith("cpio:")]
