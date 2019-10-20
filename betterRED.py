#!/usr/bin/python3

import os
import argparse
import subprocess
from distutils.dir_util import copy_tree

from tinytag import TinyTag

def main():
    args = parse_args()
    transcode(args.flac_path)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('flac_path', help='Path to flac folder')

    return parser.parse_args()

def transcode(flac_path):

    # copy everything to new destination
    output_folder_parent = '~/uploads/music'

    for root, dirs, files in os.walk(flac_path):
        for file in files:
            if file.endswith('.flac'):
                tag = TinyTag.get(os.path.join(root, file))
                output_folder = (tag.albumartist + ' - ' + tag.album
                                 + ' (' + tag.year + ') ' + ' [MP3 320]')
                break

    output_path = os.path.expanduser(os.path.join(output_folder_parent, output_folder))

    # temporary check if output path exists (usually just break altogether)
    if not os.path.exists(output_path):
        copy_tree(flac_path, output_path)

    # transcode all flac files
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if file.endswith('.flac'):
                # transcode
                flac_file = os.path.join(root, file)
                mp3_file = os.path.join(root, file.replace('.flac', '.mp3'))
                subprocess.run(['ffmpeg',
                                '-i', flac_file,
                                '-ab', '320k',
                                mp3_file])
                os.remove(flac_file)


if __name__ == "__main__":
    main()
