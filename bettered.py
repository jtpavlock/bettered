#!/usr/bin/env python3

"""Script to transcode flac to mp3 and create a torrent file.

BetteRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

Example:
    $ bettered v0 320 "Abbey Road [FLAC]/"
"""

import argparse
import logging
import os
import shlex
import subprocess
import sys
from itertools import islice
from pathlib import Path

from moe import config
from moe.library import Album
from moe_transcode import transcode

LOGGER = logging.getLogger(__name__)

LOG_LVL_ARG_MAP = {
    "none": logging.CRITICAL + 1,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
BITRATE_ARG_MAP = {
    "v0": "mp3 v0",
    "320": "mp3 320",
}


def main():
    """Run that shit."""
    args = parse_args()
    logging.basicConfig(level=LOG_LVL_ARG_MAP[args.log_level])

    try:
        config.Config(config_dir=Path.home() / ".config" / "bettered", init_db=False)
    except config.ConfigValidationError as err:
        LOGGER.error("Error reading the configuration file.")
        raise SystemExit(1) from err

    for bitrate in islice(args.bitrates, 2):  # limit to max two bitrates
        bitrate = BITRATE_ARG_MAP[bitrate]
        album = Album.from_dir(Path(args.flac_dir))

        config.CONFIG.settings.move.album_path += f" [{bitrate.upper()}]"

        transcode_album = transcode(album, bitrate)
        make_torrent(transcode_album)


def parse_args():
    """Parses and returns commandline arguments."""
    LOGGER.debug("Parsing commandline arguments: %s", sys.argv)

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
    parser.add_argument(
        "-l",
        "--log_level",
        default="info",
        choices=LOG_LVL_ARG_MAP.keys(),
        help='Logging level to output. Default is "info".\n',
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

    torrent_file = torrent_path / f"{album.artist} - {album.path.name}.torrent"
    LOGGER.info(f'Making torrent file "{torrent_file}"')

    if torrent_file.exists():
        raise FileExistsError(f'Torrent file "{torrent_file}" already exists.')

    announce_url = (
        "https://flacsfor.me/"
        f"{config.CONFIG.settings.bettered.redacted_announce_id}"
        "/announce"
    )

    torrent_cmd = (
        f"mktorrent -l 17 -p -s RED -a {announce_url} "
        f'"{album.path}" -o "{torrent_file}"'
    )

    subprocess.run(shlex.split(torrent_cmd), check=True, stdout=open(os.devnull))


if __name__ == "__main__":
    main()
