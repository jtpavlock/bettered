"""Test module for config module."""

from configparser import ConfigParser
from unittest import mock
import pytest

from bettered import config as Config


class TestReadConfig():
    """Test config.read_config()"""

    @staticmethod
    def test_config_file_exists():
        """Test FileNotFoundError if given configuration not file found."""
        with pytest.raises(FileNotFoundError):
            Config.read_config('not_a_real_config.ini')

    @staticmethod
    def test_config_locations_exist():
        """Test FileNotFoundError if no files in CONFIG_LOCATIONS found."""
        with mock.patch('bettered.config.CONFIG_LOCATIONS', ''):
            with pytest.raises(FileNotFoundError):
                Config.read_config()

    @staticmethod
    def test_success(tmpdir, caplog):
        """Test everything goes well with a valid config file."""
        tmp_file = tmpdir.mkdir('read_config').join('config.ini')
        tmp_file.write("[test]")

        with mock.patch('bettered.config.check_config'):
            Config.check_config = mock.Mock()

            config = Config.read_config(tmp_file)

            Config.check_config.assert_called_once_with(config)
            assert isinstance(config, ConfigParser)
            for record in caplog.records:
                assert record.levelname == 'DEBUG'


class TestCheckConfig():
    """Test config.check_config()"""

    @staticmethod
    @pytest.fixture(name='gen_config')
    def fixture_gen_config(tmp_path_factory):
        """Generate and return a valid ConfigParser config."""
        tmp_transcode_parent_dir = tmp_path_factory.mktemp(
            'transcode_parent_test_dir')
        tmp_torrent_file_dir = tmp_path_factory.mktemp(
            'torrent_file_test_dir')

        config = ConfigParser()
        config['main'] = {}
        config['main']['transcode_parent_dir'] = str(tmp_transcode_parent_dir)
        config['main']['torrent_file_dir'] = str(tmp_torrent_file_dir)
        config['redacted'] = {}
        config['redacted']['announce_id'] = '12345'

        return config

    @staticmethod
    def test_main_section_exists(gen_config):
        """Test KeyError if no [main] section in config."""
        config = gen_config
        config.remove_section('main')

        with pytest.raises(KeyError):
            Config.check_config(config)

    @staticmethod
    def test_transcode_parent_dir_option_exists(gen_config):
        """Test KeyError if no transcode_parent_dir option in config."""
        gen_config.remove_option('main', 'transcode_parent_dir')

        with pytest.raises(KeyError):
            Config.check_config(gen_config)

    @staticmethod
    def test_torrent_file_dir_option_exists(gen_config):
        """Test KeyError if no torrent_file_dir option in config."""
        gen_config.remove_option('main', 'torrent_file_dir')

        with pytest.raises(KeyError):
            Config.check_config(gen_config)

    @staticmethod
    def test_transcode_parent_dir_value_given(gen_config):
        """Test ValueError if no transcode_parent_dir value given."""
        gen_config.set('main', 'transcode_parent_dir', '')

        with pytest.raises(ValueError):
            Config.check_config(gen_config)

    @staticmethod
    def test_torrent_file_dir_value_given(gen_config):
        """Test ValueError if no torrent_file_dir value given."""
        gen_config.set('main', 'torrent_file_dir', '')

        with pytest.raises(ValueError):
            Config.check_config(gen_config)

    @staticmethod
    def test_valid_transcode_parent_dir(gen_config):
        """Test NotADirectoryError if transcode_parent_dir doesn't exist."""
        gen_config.set('main', 'transcode_parent_dir', 'bad_dir')

        with pytest.raises(NotADirectoryError):
            Config.check_config(gen_config)

    @staticmethod
    def test_valid_torrent_file_dir(gen_config):
        """Test NotADirectoryError if torrent_file_dir doesn't exist."""
        gen_config.set('main', 'transcode_parent_dir', 'bad_dir')

        with pytest.raises(NotADirectoryError):
            Config.check_config(gen_config)

    @staticmethod
    def test_redacted_section_exists(gen_config):
        """Test KeyError if no [redacted] section in config."""
        gen_config.remove_section('redacted')

        with pytest.raises(KeyError):
            Config.check_config(gen_config)

    @staticmethod
    def test_announce_id_option_exists(gen_config):
        """Test KeyError if no announce_id option in config."""
        gen_config.remove_option('redacted', 'announce_id')

        with pytest.raises(KeyError):
            Config.check_config(gen_config)

    @staticmethod
    def test_annouce_id_value_given(gen_config):
        """Test ValueError if no announce_id value given."""
        gen_config.set('redacted', 'announce_id', '')

        with pytest.raises(ValueError):
            Config.check_config(gen_config)

    @staticmethod
    def test_valid_config(gen_config):
        """Make sure read_config works with a valid config."""
        Config.check_config(gen_config)
