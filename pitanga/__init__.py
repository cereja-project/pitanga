from cereja import get_version_pep440_compliant

from .database.operations import *

VERSION = "0.0.2.final.0"
__version__ = get_version_pep440_compliant(VERSION)
