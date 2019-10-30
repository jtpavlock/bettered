"""Parse and check the configuration file."""

from configparser import ConfigParser
import logging
import os

LOGGER = logging.getLogger(__name__)


def read_config() -> ConfigParser:
    """Process and check a given configuration file.
    Raises:
        FileNotFoundError: No configuration file found.
        ValueError: Configuration value error.
    Returns:
        Complete ConfigParser object.
    """

    # locations to check for a configuation file (will check in list order)
    config_locations = [os.path.expanduser('~/.config/betterRED/config.ini')]

    config = ConfigParser()

    files_read = config.read(config_locations)
    if not files_read:
        raise FileNotFoundError('No configuration file found')

    _check_config(config)

    return config


def _check_config(config: ConfigParser):
    """Checks the configuration file for valid entries.
    Args:
        config: Initialized ConfigParser object.
    Raises:
        ValueError: Configuration value error.
    """
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
