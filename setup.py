#!/usr/bin/env python3
"""Define project and dependencies"""

from distutils.core import setup

setup(
    name='bettered',
    version='0.1.2',
    description='Automatic helper for redacted better.php',
    url='https://github.com/jtpavlock/betterRED',
    packages=[
        'bettered',
    ],
    entry_points={
        'console_scripts': [
            'bettered = bettered:main',
            ],
        },
    install_requires=['mutagen'],
    python_requires='>=3.6',
    )
