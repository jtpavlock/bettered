#!/usr/bin/env python3

"""Script to transcode flac to mp3 and create a torrent file.

BetterRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

Example:
    $ betterRED v0 320 "Abbey Road [FLAC]/"

"""

import argparse
from configparser import ConfigParser
from distutils.dir_util import copy_tree
import os
import shlex
import subprocess

from tinytag import TinyTag


def main():
    """Run that shit."""
    args = parse_args()
    config = ConfigParser()
    config.read(os.path.expanduser('~/.config/betterRED/config.ini'))
    check_config(config)

    for mp3_bitrate in args.mp3_bitrate:
        mp3_dir = create_pathname(args.flac_dir, mp3_bitrate,
                                  config.get('transcode', 'output_dir'))

        transcode(args.flac_dir, mp3_bitrate, mp3_dir)

        torrent_dir = os.path.join(config.get('torrent', 'torrent_file_dir'),
                                   os.path.basename(mp3_dir))
        make_torrent(mp3_dir, torrent_dir,
                     config.get('redacted', 'announce_id'))


def parse_args():
    """Parses and returns commandline arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    parser.add_argument('mp3_bitrate', choices=['V0', '320'], nargs='+',
                        help='MP3 type to transcode to (default: MP3 320)')
    parser.add_argument('flac_dir', help='Path to flac folder')

    return parser.parse_args()


def check_config(config: ConfigParser):
    """Checks the configuration file for valid entries."""
    output_dir = config.get('transcode', 'output_dir')
    if not os.path.exists(output_dir):
        raise NotADirectoryError(
            f'The provided output directory {output_dir} does not exist')

    torrent_file_dir = config.get('torrent', 'torrent_file_dir')
    if not os.path.exists(torrent_file_dir):
        raise NotADirectoryError(
            f'The provided torrent file directory {torrent_file_dir} '
            f'does not exist')


def create_pathname(flac_dir: str, mp3_bitrate: str, parent_dir: str) -> str:
    """Creates a pathname with a album-formatted basename and given parent dir.

    Uses embedded metadata to name the basename directory as such:
    'AlbumArtist - Album (Year) [MP3 mp3_bitrate]'

    Args:
        flac_dir: Directory containing a flac to grab metadata tags from.
        mp3_bitrate: Mp3 bitrate (used in directory name formatting)
        parent_dir: Parent directory to be combined with the created basename.

    Returns:
        The full pathname.
    """
    for root, __, files in os.walk(flac_dir):
        for file in files:
            if file.endswith('.flac'):
                tags = TinyTag.get(os.path.join(root, file))

                basename = (f'{tags.albumartist} - {tags.album} ({tags.year})'
                            f' [MP3 {mp3_bitrate}]')
                return os.path.join(parent_dir, basename)

    raise Exception(f'No flac files were found in {flac_dir}')


# TODO: parallize with Popen
def transcode(flac_dir: str, mp3_bitrate: str, mp3_dir: str):
    """Transcode flac dir to mp3.

    Transcodes a given directory of flac files to specified mp3 bitrate and
    renames the directory according to a given title. Also copies all non-flac
    files (e.g. cue, log, images, etc.) to the resulting directory.
    Intended to be used with an album of flacs.

    Args:
        flac_dir: Path to directory containing flac files to be converted.
        mp3_bitrate: Mp3 bitrate to transcode to.
            Supported: V0, 320
        mp3_dir: Where to store the new mp3 files.

    Raises:
        Exception: If mp3_dir already exists.
    """

    if os.path.exists(mp3_dir):
        raise IsADirectoryError(f'Output directory {mp3_dir} already exists')

    copy_tree(flac_dir, mp3_dir)  # copy everything over

    transcode_opts = '-aq 0' if mp3_bitrate == 'V0' else '-ab 320k'

    # transcode all flac files
    for root, __, files in os.walk(mp3_dir):
        for file in files:
            if file.endswith('.flac'):
                flac_file = os.path.join(root, file)
                mp3_file = flac_file.replace('.flac', '.mp3')

                # use ffmpeg to transcode
                transcode_cmd = (f'ffmpeg -i "{flac_file}" {transcode_opts}'
                                 f' "{mp3_file}"')

                subprocess.run(shlex.split(transcode_cmd), check=True)

                os.remove(flac_file)


def make_torrent(input_dir: str, torrent_dir: str, announce_id: str):
    """Makes torrent file for a given directory for upload to redacted.

    Args:
        input_dir: Directory of music files to create the torrent from.
        torrent_dir: Directory to store the torrent file.
        announce_id: User announce id to use when creating the torrent.
    """

    announce_url = f'https://flacsfor.me/{announce_id}/announce'

    torrent_cmd = (f'mktorrent -l 17 -p -s RED -a {announce_url} "{input_dir}"'
                   f' -o "{torrent_dir}.torrent"')

    subprocess.run(shlex.split(torrent_cmd), check=True)


if __name__ == "__main__":
    main()
