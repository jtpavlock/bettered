"""Module for transcoding operations."""

from distutils.dir_util import copy_tree
import logging
import os
import re
import shlex
import subprocess

from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3 as MP3

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-locals
def transcode(flac_dir: str, transcode_parent_dir: str, bitrate: str) -> str:
    """Transcode flac dir to mp3.

    Transcodes a given directory of flac files to specified mp3 bitrate and
    renames the directory according to a given title. Also copies all non-flac
    files (e.g. cue, log, images, etc.) to the resulting directory.
    Intended to be used with an album of flacs.

    Args:
        flac_dir: Path to directory containing flac files to be converted.
        transcode_parent_dir: Where to store transcoded files.
        bitrate: Bitrate to transcode to.
            See bitrate_arg_map for possible values.

    Returns:
        Full pathname of newly transcoded directory.

    Raises:
        ChildProcessError: One of the transcoding subprocesses failed.
    """
    transcode_dir = _create_album_path(flac_dir, bitrate, transcode_parent_dir)

    # first copy everything over and then transcode in place.
    LOGGER.debug('Copying "%s" to "%s"', flac_dir, transcode_dir)
    copy_tree(flac_dir, transcode_dir)

    LOGGER.info('Transcoding "%s" to "%s"', flac_dir, bitrate)

    encoding_opts = {
        'MP3 320': '-q 0 -b 320 --noreplaygain --add-id3v2',
        'MP3 V0':  '-q 0 -V 0 --vbr-new --noreplaygain --add-id3v2'
    }

    # transcode all flac files
    processes = []
    for root, _, files in os.walk(transcode_dir):
        for file in files:
            if file.endswith('.flac'):
                flac_file = os.path.join(root, file)
                transcode_file = flac_file.replace('.flac', '.mp3')
                tags = FLAC(flac_file)

                transcode_cmd = (f'lame {encoding_opts[bitrate]} '
                                 f'--tt "{_get_tag("title", tags)}" '
                                 f'--tl "{_get_tag("album", tags)}" '
                                 f'--ta "{_get_tag("artist", tags)}" '
                                 f'--tn "{_get_tag("track", tags)}" '
                                 f'--tg "{_get_tag("genre", tags)}" '
                                 f'--ty "{_get_tag("date", tags)}" '
                                 f'--tc "{_get_tag("comment", tags)}" '
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
            raise ChildProcessError(err)

    # remove flac files from new mp3 directory
    for root, _, files in os.walk(transcode_dir):
        for file in files:
            if (file.endswith('.flac')
                    or file.endswith('.cue')
                    or file.endswith('.log')
                    or file.endswith('.m3u')):
                os.remove(os.path.join(root, file))

    _check_formatting(transcode_dir)

    return transcode_dir


def _create_album_path(flac_dir: str, bitrate: str, parent_dir: str) -> str:
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
        IsADirectoryError: The generated album path already exists.
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

                album_path = os.path.join(parent_dir, basename)

                if os.path.exists(album_path):
                    raise IsADirectoryError(
                        f'Output directory "{album_path}" already exists.')

                return album_path

    raise FileNotFoundError(f'No flac files were found in {flac_dir}')


def _check_formatting(transcode_dir: str):
    """Check formatting of transcoded mp3s before uploading

    Makes sure the transcoded mp3s have the required tags and formatting
    required by redacted (https://redacted.ch/rules.php?p=upload#h2.3)

    Args:
        transcode_dir: Directory of transcoded mp3s to check

    Raises:
        ValueError: If formatting rule not followed.
    """
    # redacted required tags for any upload
    req_tags = ['artist', 'album', 'title', 'tracknumber']

    for root, _, files in os.walk(transcode_dir):
        for file in files:
            # check path length (<= 180)
            path = os.path.join(root, file).replace(
                os.path.dirname(transcode_dir), '')
            if len(path) > 180:
                raise ValueError(
                    f'The path "{path}" exceeds the 180 character limit')

            # check required tags are found
            if file.endswith('.mp3'):
                tags = MP3(os.path.join(root, file))
                for req_tag in req_tags:
                    if req_tag not in tags.keys():
                        raise ValueError(
                            f'"{file}" is missing the required tag: {req_tag}')


def _get_tag(tag_key: str, tags: dict) -> str:
    """Wrapper for mutagen tag retrieval.

    Args:
        tag_key: Tag we want to return.
        tags: Mutagen "dictionary" tags.

    Returns:
        Corresponding tag value to tag_key.
    """
    return tags[tag_key][0] if tags.get(tag_key) else ''
