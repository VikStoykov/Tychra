__version__ = "1.1.0"
__release_date__ = "2025-11-23"
__author__ = "VikStoykov"
__license__ = "MIT"
__description__ = "Tychra Discord Bot - Track market sentiment indicators"

VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable",
    "build": "20251123"
}


def get_version():
    return __version__


def get_full_version():
    return f"{__version__} ({VERSION_INFO['release']}) - {__release_date__}"


def get_version_info():
    return {
        "version": __version__,
        "release_date": __release_date__,
        "author": __author__,
        "license": __license__,
        "description": __description__,
        **VERSION_INFO
    }
