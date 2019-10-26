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
from distutils.dir_util import copy_tree, remove_tree
import logging
import os
import shlex
import subprocess
import sys

from tinytag import TinyTag

LOGGER = logging.getLogger(__name__)


class FormattingError(Exception):
    """Used for checking mp3 formatting prior to uploading"""


def main():
    """Run that shit."""
    logging.basicConfig(level=logging.INFO)

    args = parse_args()
    config = ConfigParser()
    config.read(os.path.expanduser('~/.config/betterRED/config.ini'))
    check_config(config)

    for mp3_bitrate in args.mp3_bitrate:
        try:
            mp3_dir = create_pathname(args.flac_dir, mp3_bitrate,
                                      config.get('transcode', 'output_dir'))
        except FileNotFoundError as error:
            LOGGER.error(error)
            sys.exit(1)

        try:
            transcode(args.flac_dir, mp3_bitrate, mp3_dir)
        except IsADirectoryError as error:
            LOGGER.error(error)
            sys.exit(1)

        try:
            check_formatting(mp3_dir)
        except FormattingError as error:
            remove_tree(mp3_dir)
            LOGGER.error(error)
            sys.exit(1)

        torrent_file_name = os.path.join(
            config.get('torrent', 'torrent_file_dir'),
            os.path.basename(mp3_dir)) + '.torrent'

        try:
            make_torrent(mp3_dir, torrent_file_name,
                         config.get('redacted', 'announce_id'))
        except FileExistsError as error:
            LOGGER.error(error)
            sys.exit(1)


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

    Raises:
        FileNotFoundError: A flac file wasn't found in the given flac_dir.
    """
    for root, __, files in os.walk(flac_dir):
        for file in files:
            if file.endswith('.flac'):
                tags = TinyTag.get(os.path.join(root, file))

                # default to using albumartist over artist unless it's empty
                if tags.albumartist is None:
                    albumartist = tags.artist
                else:
                    albumartist = tags.albumartist

                basename = (f'{albumartist} - {tags.album} ({tags.year})'
                            f' [MP3 {mp3_bitrate}]')
                return os.path.join(parent_dir, basename)

    raise FileNotFoundError(f'No flac files were found in {flac_dir}')


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
        IsADirectoryError: If mp3_dir already exists.
    """
    if os.path.exists(mp3_dir):
        raise IsADirectoryError(
            f'Output directory "{mp3_dir}" already exists.')

    copy_tree(flac_dir, mp3_dir)  # copy everything over

    transcode_opts = '-aq 0' if mp3_bitrate == 'V0' else '-ab 320k'

    # transcode all flac files
    LOGGER.info('Transcoding "%s"', flac_dir)
    processes = []
    for root, _, files in os.walk(mp3_dir):
        for file in files:
            if file.endswith('.flac'):
                flac_file = os.path.join(root, file)
                mp3_file = flac_file.replace('.flac', '.mp3')

                # use ffmpeg to transcode
                transcode_cmd = (f'ffmpeg -loglevel error -i "{flac_file}" '
                                 f'{transcode_opts} "{mp3_file}"')

                # run transocding commands in parallel
                # stdin redirect required to reset terminal
                processes.append(
                    subprocess.Popen(shlex.split(transcode_cmd),
                                     stdin=open(os.devnull)))

    # wait for transcodes to finish
    for process in processes:
        process.wait()

    # remove flac files from new mp3 directory
    for root, _, files in os.walk(mp3_dir):
        for file in files:
            if file.endswith('.flac'):
                os.remove(os.path.join(root, file))


def check_formatting(mp3_dir: str):
    """Check formatting of transcoded mp3s before uploading

    Makes sure the transcoded mp3s have the required tags and formatting
    required by redacted (https://redacted.ch/rules.php?p=upload#h2.3)

    Args:
        mp3_dir: Directory of transcoded mp3s to check

    Raises:
        FormattingError: If formatting rule not followed.
    """
    for root, _, files in os.walk(mp3_dir):
        for file in files:
            # check path length (<= 180)
            path = os.path.join(root, file).replace(
                os.path.dirname(mp3_dir), '')
            if len(path) > 180:
                raise FormattingError(
                    f'The path "{path}" exceeds the 180 character limit')

            # check required tags (artist, album, title, track #) are found
            if file.endswith('.mp3'):
                tags = TinyTag.get(os.path.join(root, file))
                if tags.artist is None:
                    raise FormattingError(
                        f'The file "{file}" has no artist tag')
                if tags.album is None:
                    raise FormattingError(
                        f'The file "{file}" has no album tag')
                if tags.title is None:
                    raise FormattingError(
                        f'The file "{file}" has no title tag')
                if tags.track is None:
                    raise FormattingError(
                        f'The file "{file}" has no track number tag')


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
            f'Torrent file"{torrent_file_name}" already exists.')

    announce_url = f'https://flacsfor.me/{announce_id}/announce'

    torrent_cmd = (f'mktorrent -l 17 -p -s RED -a {announce_url} "{input_dir}"'
                   f' -o "{torrent_file_name}.torrent"')

    subprocess.run(shlex.split(torrent_cmd), check=True,
                   stdout=open(os.devnull))


if __name__ == "__main__":
    main()
