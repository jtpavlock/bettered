"""Module for dealing with Album class to include transcoding and
torrent creation.
"""

from distutils.dir_util import copy_tree
import logging
import os
import re
import shlex
import subprocess

import mutagen

LOGGER = logging.getLogger(__name__)


class Album():
    """Represent and perform operations on an album.

    An "album" is a directory of music files that could also be
    considered a single torrent. This means for our purposes, directories
    representing a single, EP, compilation, etc. are all considered albums.
    """
    def __init__(self, path: str):
        self.path = path

    # pylint: disable=too-many-locals
    def transcode(self, transcode_parent_dir: str, bitrate: str) -> 'Album':
        """Transcodes album to bitrate and stores the result in transcode_dir.

        Intended to be used to transcode flac -> mp3 [v0, 320].
        Will spawn a process (thread) for each file to be transcoded.

        Args:
            transcode_parent_dir: Where to store transcoded album
            bitrate: Bitrate to transcode to.
                Valid bitrates: 'MP3 320', 'MP3 V0'

        Returns:
            Transcoded Album class object.

        Raises:
            ChildProcessError: One of the transcoding subprocesses failed.
            IsADirectoryError: transcode_dir already exists
        """

        transcode_dir = os.path.join(
            transcode_parent_dir, self._make_base_dir(bitrate))

        if os.path.exists(transcode_dir):
            raise IsADirectoryError('The attempted transcode directory '
                                    f'"{transcode_dir}" already exists.')

        # first copy everything over and then transcode in place.
        LOGGER.debug('Copying "%s" to "%s"', self.path, transcode_dir)
        copy_tree(self.path, transcode_dir)

        encoding_opts = {
            'MP3 320': '-q 0 -b 320 --noreplaygain --add-id3v2',
            'MP3 V0':  '-q 0 -V 0 --vbr-new --noreplaygain --add-id3v2'
        }

        # transcode all flac files
        LOGGER.info('Transcoding "%s" to "%s"', self.path, bitrate)
        processes = []
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith('.flac'):
                    flac_file = os.path.join(root, file)
                    transcode_file = flac_file.replace('.flac', '.mp3')
                    LOGGER.debug("%s", transcode_file)

                    tags = mutagen.flac.FLAC(flac_file)
                    # lame expects a wav file, so wav -> flac | lame
                    flac_to_wav = subprocess.Popen(
                        shlex.split(f'flac -cd "{flac_file}"'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    transcode_cmd = (f'lame {encoding_opts[bitrate]} '
                                     f'--tt "{self._get_tag("title", tags)}" '
                                     f'--tl "{self._get_tag("album", tags)}" '
                                     f'--ta "{self._get_tag("artist", tags)}" '
                                     f'--tn "{self._get_tag("track", tags)}" '
                                     f'--tg "{self._get_tag("genre", tags)}" '
                                     f'--ty "{self._get_tag("date", tags)}" '
                                     f'--tc "{self._get_tag("comment", tags)}"'
                                     f' "{flac_file}" "{transcode_file}"')

                    # run transocding commands in parallel
                    processes.append(subprocess.Popen(
                        shlex.split(transcode_cmd), stdin=flac_to_wav.stdout,
                        stderr=subprocess.PIPE))

        # wait for transcodes to finish
        for process in processes:
            err = process.communicate()[1]
            if process.returncode:
                # a transcoding processes failed - raise with stderr msg
                raise ChildProcessError(err)

        # remove flac, cue, log, and m3u files from new mp3 directory
        for root, _, files in os.walk(transcode_dir):
            for file in files:
                if file.endswith(('.flac', '.cue', '.log', '.m3u')):
                    os.remove(os.path.join(root, file))

        return Album(transcode_dir)

    def make_torrent(self, torrent_file_dir: str, passkey: str):
        """Makes torrent file for a given directory for upload to redacted.

        Args:
            torrent_file_dir: Where to store resulting torrent file.
            passkey: Redacted user passkey (aka announce_id in config)

        Raises:
            FileExistsError: If torrent_file already exists.
        """
        self._check_red_formatting()

        torrent_file = (os.path.join(
            torrent_file_dir, os.path.basename(self.path)) + '.torrent')
        LOGGER.info('Making torrent file "%s"', torrent_file)

        if os.path.exists(torrent_file):
            raise FileExistsError(
                f'Torrent file "{torrent_file}" already exists.')

        announce_url = f'https://flacsfor.me/{passkey}/announce'

        torrent_cmd = (f'mktorrent -l 17 -p -s RED -a {announce_url} '
                       f'"{self.path}" -o "{torrent_file}"')

        subprocess.run(shlex.split(torrent_cmd), check=True,
                       stdout=open(os.devnull))

    def _check_red_formatting(self):
        """Check formatting of an album based on redacted requirements.

        Makes sure all the tags and formatting rules are abided by
        https://redacted.ch/rules.php?p=upload#h2.3

        Raises:
            ValueError: If formatting rule not followed.
        """
        LOGGER.debug('Checking "%s" for required redacted formatting',
                     self.path)

        req_tags = ['artist', 'album', 'title', 'tracknumber']

        for root, _, files in os.walk(self.path):
            for file in files:
                # check path length (<= 180)
                path = os.path.join(root, file).replace(
                    os.path.dirname(self.path), '')
                if len(path) > 180:
                    raise ValueError(
                        f'The path "{path}" exceeds the 180 character limit')

                # check required tags are found
                if file.endswith('.mp3'):
                    mp3_file = os.path.join(root, file)
                    tags = mutagen.mp3.EasyMP3(mp3_file)
                    for req_tag in req_tags:
                        if req_tag not in tags.keys():
                            raise ValueError(
                                f'"{mp3_file}" is missing the required tag: '
                                f'"{req_tag}"')

    def _make_base_dir(self, bitrate: str) -> str:
        """Creates a path basename for a given bitrate.

        Uses embedded metadata to name the basename directory as such:
        'AlbumArtist - Album (Year) [Bitrate]'

        Args:
            bitrate: Bitrate used in directory naming.

        Returns:
            The full pathname.

        Raises:
            FileNotFoundError: No music files found in self.path
            IsADirectoryError: The generated album path already exists.
            TypeError: Tag not found in music file
        """
        LOGGER.debug('Generating the transcoded album path')

        for root, __, files in os.walk(self.path):
            for file in files:
                tags = mutagen.File(os.path.join(root, file), easy=True)
                if tags:
                    try:
                        albumartist = tags.get('albumartist')[0]
                    except TypeError:
                        albumartist = tags.get('artist')[0]
                    try:
                        year = tags.get('date')[0]
                    except TypeError:
                        year = tags.get('year')[0]
                    album = tags.get('album')[0]

                    basename = (f'{albumartist} - {album} ({year}) '
                                f'[{bitrate}]')

                    # remove illegal chars (: ? < > \ * | " // (Leading Space))
                    basename = re.sub('[:?<>\\*|"//]', ' ', basename)
                    LOGGER.debug('Generated album path: %s', basename)

                    return basename

        raise FileNotFoundError(f'No music files were found in {self.path}')

    @staticmethod
    def _get_tag(tag_key: str, tags: dict) -> str:
        """Wrapper for safe mutagen tag retrieval.

        Args:
            tag_key: Tag we want to return.
            tags: Mutagen "dictionary" tags.

        Returns:
            Corresponding tag value to tag_key.
        """
        return tags[tag_key][0] if tags.get(tag_key) else ''
