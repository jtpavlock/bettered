#!/usr/bin/python3

import os
import argparse
import subprocess
from distutils.dir_util import copy_tree

from tinytag import TinyTag

def main():
    args = parse_args()

    for mp3_type in args.mp3_type:
        transcode(args.flac_path, mp3_type)

# TODO: add option for 320 vs v0
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('mp3_type', choices=['v0','320'], nargs='+',
                        help='MP3 type to transcode to (default: MP3 320)')
    parser.add_argument('flac_path', help='Path to flac folder')

    return parser.parse_args()

def transcode(flac_path, mp3_type):

    # copy everything to new destination
    output_folder_parent = '~/uploads/music'

    for root, dirs, files in os.walk(flac_path):
        for file in files:
            if file.endswith('.flac'):
                tag = TinyTag.get(os.path.join(root, file))
                output_folder = (tag.albumartist + ' - ' + tag.album
                                 + ' (' + tag.year + ') '
                                 + ' [MP3 ' + mp3_type + ']')
                break

    output_path = os.path.expanduser(os.path.join(output_folder_parent, output_folder))

    # temporary check if output path exists (usually just break altogether)
    if not os.path.exists(output_path):
        copy_tree(flac_path, output_path)

    transcode_opts = ['-aq', '0'] if mp3_type is 'V0' else ['-ab', '320k']

    # transcode all flac files
    os.chdir(output_path)
    print(os.getcwd())
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if file.endswith('.flac'):
                # transcode
                f = os.path.join(root, file)
                mp3_file = os.path.join(root, f.replace('.flac', '.mp3'))
                subprocess.run(['ffmpeg',
                                '-i', f] + transcode_opts
                               + [f.replace('.flac', '.mp3')])
                os.remove(f)

if __name__ == "__main__":
    main()
