#!/usr/bin/env python3

"""Script to transcode flac to mp3 and create a torrent file.

BetterRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

Example:
    $ betterRED v0 320 "Abbey Road [FLAC]/"

"""

import argparse
import logging
import os
import shlex
import subprocess
import sys


from bettered.config import read_config
from bettered.transcode import transcode

LOGGER = logging.getLogger(__name__)


def main():
    """Run that shit."""
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()
    config = read_config()

    bitrate_arg_map = {'v0': 'MP3 V0', '320': 'MP3 320'}

    for bitrate_arg in args.bitrates:
        bitrate = bitrate_arg_map[bitrate_arg]

        transcode_parent_dir = config.get('main', 'transcode_parent_dir')

        transcode_dir = transcode(os.path.abspath(args.flac_dir),
                                  transcode_parent_dir, bitrate)

        torrent_file_name = os.path.join(
            config.get('main', 'torrent_file_dir'),
            os.path.basename(transcode_dir)) + '.torrent'

        make_torrent(transcode_dir, torrent_file_name,
                     config.get('redacted', 'announce_id'))


def parse_args():
    """Parses and returns commandline arguments."""
    LOGGER.debug('Parsing commandline arguments: %s', sys.argv)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    parser.add_argument('bitrates', choices=['v0', '320'], nargs='+',
                        help='MP3 bitrate to transcode to.')
    parser.add_argument('flac_dir',
                        help='Path to flac directory containing files to be '
                        'transcoded')

    return parser.parse_args()


def make_torrent(input_dir: str, torrent_file_name: str, announce_id: str):
    """Makes torrent file for a given directory for upload to redacted.

    Args:
        input_dir: Directory of music files to create the torrent from.
        torrent_file_name: Absolute (full path) name for new torrent file.
        announce_id: User announce id to use when creating the torrent.

    Raises:
        FileExistsError: If torrent_file_name already exists.
    """
    LOGGER.info('Making torrent file "%s"', torrent_file_name)

    if os.path.exists(torrent_file_name):
        raise FileExistsError(
            f'Torrent file "{torrent_file_name}" already exists.')

    announce_url = f'https://flacsfor.me/{announce_id}/announce'

    torrent_cmd = (f'mktorrent -l 17 -p -s RED -a {announce_url} "{input_dir}"'
                   f' -o "{torrent_file_name}"')

    subprocess.run(shlex.split(torrent_cmd), check=True,
                   stdout=open(os.devnull))


if __name__ == "__main__":
    main()
