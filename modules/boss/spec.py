from __future__ import absolute_import
import warnings
from .rpm import parse_spec  # noqa

warnings.warn('boss.spec module is deprecated, use boss.rpm instead')
