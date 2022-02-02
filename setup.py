#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package metadata for learnupon_exporter.
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import sys

from setuptools import setup

def read_file(filename):
    """
    Reads and return filename's data.

    Method exists solely to safe file reading.
    """
    with open(filename, encoding='utf8') as fo:
        return fo.read()

def read_file_lines(filename):
    """
    Reads the lines in a file.

    Method exists solely to safe file reading.
    """
    with open(filename, encoding='utf8') as fo:
        return fo.readlines()

def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = read_file(filename)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split("#")[0].strip()
            for line in read_file_lines(path)
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included file
    """
    return not (
        line == ""
        or line.startswith("-r")
        or line.startswith("#")
        or line.startswith("-e")
        or line.startswith("git+")
    )


VERSION = get_version("learnupon_exporter", "__init__.py")

if sys.argv[-1] == "tag":
    print("Tagging the version on github:")
    os.system(f"git tag -a {VERSION} -m 'version {VERSION}'")
    os.system("git push --tags")
    sys.exit()

README = read_file(os.path.join(os.path.dirname(__file__), "README.md"))

setup(
    name="learnupon-exporter",
    version=VERSION,
    description="""Django plugin application to export edX data to LearnUpon.""",
    long_description=README,
    author="OpenCraft",
    author_email="help@opencraft.com",
    url="https://github.com/open-craft/learnupon-exporter",
    packages=[
        "learnupon_exporter",
    ],
    include_package_data=True,
    install_requires=load_requirements("requirements/base.in"),
    license="AGPL 3.0",
    zip_safe=False,
    keywords="Django edx",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django",
        "Framework :: Django :: 1.8",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        "cms.djangoapp": [
            "learnupon_exporter = learnupon_exporter.apps:LearnUponExporterAppConfig",
        ],
    },
)
