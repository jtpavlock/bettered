#!/usr/bin/env python3
"""Define project and dependencies"""

from distutils.core import setup

with open('README.md', 'r') as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='bettered',
    version='0.2.3',
    description='Automatic helper for redacted better.php',
    long_description=LONG_DESCRIPTION,
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
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'pylint',
            ]
        },
    python_requires='>=3.6',
    )
