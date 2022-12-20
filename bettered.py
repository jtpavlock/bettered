#!/usr/bin/env python3

"""Script to transcode flac to mp3 and create a torrent file.

BetteRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

Example:
    $ bettered v0 320 "Abbey Road [FLAC]/"
"""

import argparse
import os
import shlex
import subprocess
from itertools import islice
from pathlib import Path

from moe import config
from moe.library import Album
from moe.plugins.move import fmt_item_path
from moe_transcode import transcode

BITRATE_ARG_MAP = {
    "v0": "mp3 v0",
    "320": "mp3 320",
}


def main():
    """Run that shit."""
    args = parse_args()

    try:
        config.Config(config_dir=Path.home() / ".config" / "bettered", init_db=False)
    except config.ConfigValidationError as err:
        print("Error reading configuration file.")
        raise SystemExit(1) from err

    for bitrate in islice(args.bitrates, 2):  # limit to max two bitrates
        bitrate = BITRATE_ARG_MAP[bitrate]
        album = Album.from_dir(Path(args.flac_dir))

        transcode_path = Path(
            config.CONFIG.settings.transcode.transcode_path
        ).expanduser()
        out_path = fmt_item_path(album, lib_path=transcode_path)
        out_path = Path(str(out_path) + f" [{bitrate.upper()}]")

        print(f"Transcoding '{album}' to '{bitrate.upper()}'")
        transcode_album = transcode(album, bitrate, out_path)

        make_torrent(transcode_album)


def parse_args():
    """Parses and returns commandline arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__
    )

    parser.add_argument(
        "bitrates",
        choices=["v0", "320"],
        nargs="+",
        help="MP3 bitrate to transcode to.",
    )
    parser.add_argument(
        "flac_dir",
        type=os.path.abspath,
        help="Path to flac directory containing files to be " "transcoded",
    )

    return parser.parse_args()


def make_torrent(album: Album):
    """Makes torrent file for a given directory for upload to redacted.

    Args:
        album: Album to create the torrent from.

    Raises:
        FileExistsError: If torrent_file already exists.
    """
    torrent_path = Path(config.CONFIG.settings.bettered.torrent_file_path).expanduser()
    torrent_path.mkdir(parents=True, exist_ok=True)

    torrent_file = torrent_path / f"{album.path.name}.torrent"
    print(f"Making torrent file {torrent_file}")

    if torrent_file.exists():
        raise FileExistsError(f'Torrent file "{torrent_file}" already exists.')

    torrent_cmd = (
        f"mktorrent -l 17 -p -s RED -a {config.CONFIG.settings.bettered.announce_url} "
        f'"{album.path}" -o "{torrent_file}"'
    )

    subprocess.run(shlex.split(torrent_cmd), check=True, stdout=open(os.devnull))


if __name__ == "__main__":
    main()
