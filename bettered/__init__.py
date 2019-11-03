#!/usr/bin/env python3

"""Script to transcode flac to mp3 and create a torrent file.

BetteRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

Example:
    $ bettered v0 320 "Abbey Road [FLAC]/"

"""

import argparse
from itertools import islice
import logging
import os
import sys

from bettered.config import read_config
from bettered.album import Album

LOGGER = logging.getLogger(__name__)

LOG_LVL_ARG_MAP = {
    'none': logging.CRITICAL + 1, 'debug': logging.DEBUG,
    'info': logging.INFO, 'warn': logging.WARN,
    'error': logging.ERROR, 'critical': logging.CRITICAL
}
BITRATE_ARG_MAP = {
    'v0': 'MP3 V0', '320': 'MP3 320',
}


def main():
    """Run that shit."""
    args = parse_args()
    logging.basicConfig(level=LOG_LVL_ARG_MAP[args.log_level])
    config = read_config(args.config)

    transcode_parent_dir = os.path.abspath(
        config.get('main', 'transcode_parent_dir'))
    torrent_file_dir = os.path.abspath(
        config.get('main', 'torrent_file_dir'))
    announce_id = config.get('redacted', 'announce_id')

    for bitrate in islice(args.bitrates, 2):  # limit to max two bitrates
        bitrate = BITRATE_ARG_MAP[bitrate]
        album = Album(args.flac_dir)

        transcode_album = album.transcode(transcode_parent_dir, bitrate)
        transcode_album.make_torrent(torrent_file_dir, announce_id)


def parse_args():
    """Parses and returns commandline arguments."""
    LOGGER.debug('Parsing commandline arguments: %s', sys.argv)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    parser.add_argument('bitrates', choices=['v0', '320'], nargs='+',
                        help='MP3 bitrate to transcode to.')
    parser.add_argument('flac_dir', type=os.path.abspath,
                        help='Path to flac directory containing files to be '
                        'transcoded')
    parser.add_argument('-c', '--config', help='Configuration file location')
    parser.add_argument('-l', '--log_level', default='info',
                        choices=LOG_LVL_ARG_MAP.keys(),
                        help='Logging level to output. Default is "info".\n')

    return parser.parse_args()


if __name__ == "__main__":
    main()
