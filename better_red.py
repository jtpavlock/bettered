#!/usr/bin/python3

"""Script to transcode flac to mp3 and create a torrent file.

BetterRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file.

Example:
    $ betterRED v0 320 "Abbey Road [FLAC]/"

Todo:
    * Finish docstrings (setup yasnippet?)
    * Clean up pylint / flake8 errors
"""

import os
import argparse
import subprocess
import shlex
from distutils.dir_util import copy_tree

from tinytag import TinyTag


def main():
    """Run that shit."""
    args = parse_args()

    for mp3_type in args.mp3_type:
        output_dir_basename = create_output_dir_basename(args.flac_path,
                                                         mp3_type)
        mp3_path = transcode(args.flac_path, mp3_type, output_dir_basename)
        make_torrent(mp3_path, output_dir_basename)


def parse_args():
    """Parses and returns commandline arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('mp3_type', choices=['v0', '320'], nargs='+',
                        help='MP3 type to transcode to (default: MP3 320)')
    parser.add_argument('flac_path', help='Path to flac folder')

    return parser.parse_args()


def create_output_dir_basename(flac_path, mp3_type):
    """Creates basename of output directory.

    Uses basic metadata from a single flac file to name the folder as such:
    'AlbumArtist - Album (Year) [Codec]'

    """

    for root, __, files in os.walk(flac_path):
        for file in files:
            if file.endswith('.flac'):
                tag = TinyTag.get(os.path.join(root, file))
                output_title = (tag.albumartist + ' - ' + tag.album
                                + ' (' + tag.year + ') '
                                + ' [MP3 ' + mp3_type + ']')
                return output_title

    raise Exception(f'No flac files were found in {flac_path}')


def transcode(flac_path, mp3_type, output_title):
    """Transcode flac to mp3"""

    output_dir = '/home/jacob/uploads/music'
    output_path = os.path.join(output_dir, output_title)

    # temporary check if output path exists (usually just break altogether)
    if not os.path.exists(output_path):
        copy_tree(flac_path, output_path)  # copy everything over

    transcode_opts = ['-aq', '0'] if mp3_type == 'V0' else ['-ab', '320k']

    # transcode all flac files
    for root, __, files in os.walk(output_path):
        for file in files:
            if file.endswith('.flac'):
                flac_file = os.path.join(root, file)

                # use ffmpeg to transcode
                subprocess.run(['ffmpeg', '-i', flac_file] + transcode_opts
                               + [flac_file.replace('.flac', '.mp3')],
                               check=True)

                os.remove(flac_file)

    return output_path


def make_torrent(mp3_path, output_title):
    """Make torrent file for transcoded mp3s."""

    announce_id = 'ef53de84b2beea212a4ee452cd9edb19'
    announce_url = f'https://flacsfor.me/{announce_id}/announce'
    torrent_dir = '/home/jacob/torrents'

    torrent_cmd = f'''mktorrent -l 17 -p -s RED -a {announce_url} "{mp3_path}"
    -o "{os.path.join(torrent_dir, output_title)}.torrent"'''

    subprocess.run(shlex.split(torrent_cmd), check=True)


if __name__ == "__main__":
    main()
