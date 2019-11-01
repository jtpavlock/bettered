"""Parse and check the configuration file."""

from configparser import ConfigParser
import logging
import os

LOGGER = logging.getLogger(__name__)

# locations to check for a configuation file (will check in list order)
CONFIG_LOCATIONS = [
    os.path.expanduser('~/.config/bettered/config.ini')
]


def read_config(config_location: str = None) -> ConfigParser:
    """Process and check a given configuration file.

    Args:
        config_location: Path to configuration file.
            If none given (via commandline argument), it will default to
            checking the preset CONFIG_LOCATIONS.

    Raises:
        FileNotFoundError: No configuration file found.
        ValueError: Configuration value error.

    Returns:
        Complete ConfigParser object.
    """
    config = ConfigParser()

    if config_location:
        config_location = os.path.expanduser(config_location)
    else:
        config_location = CONFIG_LOCATIONS

    files_read = config.read(config_location)
    if not files_read:
        raise FileNotFoundError('No configuration file at the following '
                                f'location(s): {config_location}')
    LOGGER.debug('Read config file "%s"', files_read)

    check_config(config)

    return config


def check_config(config: ConfigParser):
    """Checks the configuration file for valid entries.

    Args:
        config: Initialized ConfigParser object

    Raises:
        KeyError: Missing required configuration option
        ValueError: Invalid or no configuration value
        NotADirectoryError: Directory given doesn't exist
    """
    LOGGER.debug('Checking config file')

    # check main section exists and has required options
    if not config.has_section('main'):
        raise KeyError('No section "main" in config file')
    if not config.has_option('main', 'transcode_parent_dir'):
        raise KeyError('No option "transcode_parent_dir" found in config file')
    if not config.has_option('main', 'torrent_file_dir'):
        raise KeyError('No option "torrent_file_dir" found in config file')

    # check valid values given for main section
    if not config.get('main', 'transcode_parent_dir'):
        raise ValueError('No config value for "transcode_parent_dir" given')
    if not config.get('main', 'torrent_file_dir'):
        raise ValueError('No config value for "torrent_file_dir" given')

    transcode_parent_dir = config.get('main', 'transcode_parent_dir')
    if not os.path.exists(config.get('main', 'transcode_parent_dir')):
        raise NotADirectoryError(
            f'The provided transcode parent directory "{transcode_parent_dir}"'
            ' does not exist')

    torrent_file_dir = config.get('main', 'torrent_file_dir')
    if not os.path.exists(torrent_file_dir):
        raise NotADirectoryError(
            f'The provided torrent file directory {torrent_file_dir} '
            'does not exist')

    # check redacted section exists and has required options
    if not config.has_section('redacted'):
        raise KeyError('No section "redacted" in config file')
    if not config.has_option('redacted', 'announce_id'):
        raise KeyError('No option "announce_id" found in config file')

    # check valid values given for redacted section
    if not config.get('redacted', 'announce_id'):
        raise ValueError('No config value for "announce_id" given')
