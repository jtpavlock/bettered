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
import logging
import os
import re
import shlex
import subprocess
import sys

from mutagen.mp3 import EasyMP3 as MP3
from mutagen.flac import FLAC

from better_red import config as Config

LOGGER = logging.getLogger(__name__)


def main():
    """Run that shit."""
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()
    config = Config.read_config()

    bitrate_arg_map = {'v0': 'MP3 V0', '320': 'MP3 320'}

    for bitrate_arg in args.bitrates:
        bitrate = bitrate_arg_map[bitrate_arg]

        transcode_parent_dir = config.get('main', 'transcode_parent_dir')
        transcode_dir = create_album_path(args.flac_dir, bitrate,
                                          transcode_parent_dir)

        transcode(os.path.abspath(args.flac_dir), transcode_dir, bitrate)

        check_formatting(transcode_dir)

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

    return parser.parse_args()


def check_config(config: ConfigParser):
    """Checks the configuration file for valid entries."""
    LOGGER.debug('Checking config file')

    if not config.get('main', 'transcode_parent_dir'):
        raise ValueError('No transcode parent directory given')
    if not config.get('main', 'torrent_file_dir'):
        raise ValueError('No transcode file directory given')
    if not config.get('main', 'transcode_parent_dir'):
        raise ValueError('No music directory given')

    transcode_parent_dir = config.get('main', 'transcode_parent_dir')
    if not os.path.exists(config.get('main', 'transcode_parent_dir')):
        raise ValueError(
            f'The provided transcode parent directory {transcode_parent_dir} '
            f'does not exist')

    torrent_file_dir = config.get('main', 'torrent_file_dir')
    if not os.path.exists(torrent_file_dir):
        raise ValueError(
            f'The provided torrent file directory {torrent_file_dir} '
            f'does not exist')

    music_dir = config.get('main', 'music_dir')
    if not os.path.exists(torrent_file_dir):
        raise ValueError(
            f'The provided music directory {music_dir} does not exist')

    if not config.get('redacted', 'username'):
        raise ValueError('No redacted username given')
    if not config.get('redacted', 'password'):
        raise ValueError('No redacted password given')
    if not config.get('redacted', 'announce_id'):
        raise ValueError('No redacted announce_id given')


def create_album_path(flac_dir: str, bitrate: str, parent_dir: str) -> str:
    """Creates a pathname with an album-formatted basename and given parent dir.

    Uses embedded metadata to name the basename directory as such:
    'AlbumArtist - Album (Year) [Bitrate]'

    Args:
        flac_dir: Directory containing a flac to grab metadata tags from.
        bitrate: Bitrate used in directory naming.
        parent_dir: Parent directory to be combined with the created basename.

    Returns:
        The full pathname.

    Raises:
        FileNotFoundError: A flac file wasn't found in the given flac_dir.
    """
    LOGGER.debug('Generating the output album path')

    for root, __, files in os.walk(flac_dir):
        for file in files:
            if file.endswith('.flac'):
                tags = FLAC(os.path.join(root, file))
                LOGGER.debug('Tags used for the album path: %s', tags)

                # default to using albumartist over artist unless it's empty
                if not tags.get('albumartist'):
                    albumartist = tags['artist'][0]
                else:
                    albumartist = tags['albumartist'][0]

                # date should be the standard here but check year if empty
                if tags.get('date'):
                    year = tags['date'][0]
                elif tags.get('year'):
                    year = tags['date'][0]

                basename = (f'{albumartist} - {tags["album"][0]} '
                            f'({year}) [{bitrate}]')

                # remove illegal chars (: ? < > \ * | " // (Leading Space))
                basename = re.sub('[:?<>\\*|"//]', ' ', basename)

                LOGGER.debug('Generated album path: %s', basename)

                return os.path.join(parent_dir, basename)

    raise FileNotFoundError(f'No flac files were found in {flac_dir}')


def transcode(flac_dir: str, transcode_dir: str, bitrate: str):
    """Transcode flac dir to mp3.

    Transcodes a given directory of flac files to specified mp3 bitrate and
    renames the directory according to a given title. Also copies all non-flac
    files (e.g. cue, log, images, etc.) to the resulting directory.
    Intended to be used with an album of flacs.

    Args:
        flac_dir: Path to directory containing flac files to be converted.
        transcode_dir: Where to store transcoded files.
        bitrate: Bitrate to transcode to.
            See bitrate_arg_map for possible values.

    Raises:
        IsADirectoryError: transcode_dir already exists.
        TranscodeError: Error when transcoding.
    """
    LOGGER.info('Transcoding "%s" to "%s"', flac_dir, bitrate)

    encoding_opts = {
        'MP3 320': '-q 0 -b 320 --noreplaygain --add-id3v2',
        'MP3 V0':  '-q 0 -V 0 --vbr-new --noreplaygain --add-id3v2'
    }

    if os.path.exists(transcode_dir):
        raise IsADirectoryError(
            f'Output directory "{transcode_dir}" already exists.')

    copy_tree(flac_dir, transcode_dir)  # copy everything over

    # transcode all flac files
    processes = []
    for root, _, files in os.walk(transcode_dir):
        for file in files:
            if file.endswith('.flac'):
                flac_file = os.path.join(root, file)
                transcode_file = flac_file.replace('.flac', '.mp3')
                tags = FLAC(flac_file)

                transcode_cmd = (f'lame {encoding_opts[bitrate]} '
                                 f'--tt "{get_tag("title", tags)}" '
                                 f'--tl "{get_tag("album", tags)}" '
                                 f'--ta "{get_tag("artist", tags)}" '
                                 f'--tn "{get_tag("track", tags)}" '
                                 f'--tg "{get_tag("genre", tags)}" '
                                 f'--ty "{get_tag("date", tags)}" '
                                 f'--tc "{get_tag("comment", tags)}" '
                                 f'"{flac_file}" "{transcode_file}"')

                # run transocding commands in parallel
                processes.append(
                    subprocess.Popen(shlex.split(transcode_cmd),
                                     stderr=subprocess.PIPE))

    # wait for transcodes to finish
    for process in processes:
        err = process.communicate()[1]
        if process.returncode:
            # one of our transcoding processes failed - raise with stderr msg
            raise TranscodeError(err)

    # remove flac files from new mp3 directory
    for root, _, files in os.walk(transcode_dir):
        for file in files:
            if file.endswith('.flac'):
                os.remove(os.path.join(root, file))


def check_formatting(transcode_dir: str):
    """Check formatting of transcoded mp3s before uploading

    Makes sure the transcoded mp3s have the required tags and formatting
    required by redacted (https://redacted.ch/rules.php?p=upload#h2.3)

    Args:
        transcode_dir: Directory of transcoded mp3s to check

    Raises:
        FormattingError: If formatting rule not followed.
    """
    # redacted required tags for any upload
    req_tags = ['artist', 'album', 'title', 'tracknumber']

    for root, _, files in os.walk(transcode_dir):
        for file in files:
            # check path length (<= 180)
            path = os.path.join(root, file).replace(
                os.path.dirname(transcode_dir), '')
            if len(path) > 180:
                raise FormattingError(
                    f'The path "{path}" exceeds the 180 character limit')

            # check required tags are found
            if file.endswith('.mp3'):
                tags = MP3(os.path.join(root, file))
                for req_tag in req_tags:
                    if req_tag not in tags.keys():
                        raise FormattingError(
                            f'"{file}" is missing the required tag: {req_tag}')


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


def get_tag(tag_key: str, tags: dict) -> str:
    """Wrapper for mutagen tag retrieval.

    Args:
        tag_key: Tag we want to return.
        tags: Mutagen "dictionary" tags.

    Returns:
        Corresponding tag value to tag_key.
    """
    return tags[tag_key][0] if tags.get(tag_key) else ''


if __name__ == "__main__":
    main()
