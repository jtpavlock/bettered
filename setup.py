#!/usr/bin/env python3
"""Define project and dependencies"""

from distutils.core import setup

setup(
    name='betterRED',
    version='0.1',
    description='Automatic helper for redacted better.php',
    url='https://github.com/jtpavlock/betterRED',
    packages=[],
    install_requires=['mutagen'],
    python_requires='>=3.6',
    )
