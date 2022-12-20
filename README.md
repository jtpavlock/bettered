# BetteRED

## Introduction
bettered automatically transcodes a given path of flac files to mp3 files based on desired quality (MP3 V0 or MP3 320) and creates a corresponding torrent file with a specified announce url.

bettered uses [Moe](https://github.com/MoeMusic/Moe) to initialize and read the configuration, and the plugin [moe_transcode](https://github.com/MoeMusic/moe_transcode) to handle the transcoding logic.

## Installation:

### 1. Install `bettered` from PyPI

I recommend using [pipx](https://pypa.github.io/pipx/) to install `bettered`.
`$ pipx install bettered`

If you don't care about having `bettered` and it's dependencies (mainly `Moe`) in an isolated environment, you can just install normally with pip as well.
`$ pip install bettered`

### 2. Install `mktorrent`
`mktorrent` must be built from source unless your package manager includes >=v1.1

~~~
$ git clone https://github.com/Rudde/mktorrent.git
$ cd mktorrent
$ sudo make install
~~~

### 3. Install `ffmpeg`
https://ffmpeg.org/download.html

Run `ffmpeg -h` to ensure it's in your path.

### 4. Configure

Your configuration file should exist in "~/.config/bettered/config.toml" and should look like the following:

``` toml
enable_plugins = ["transcode"]

[transcode]
transcode_path = "~/transcode"

[bettered]
torrent_file_path = "~/torrents"
announce_url = "https://flacsfor.me/213/announce"

[move]
album_path = "{album.artist} - {album.title} ({album.year})"
```

`transcode_path` is where the transcoded albums will be placed.
`torrent_file_path` is where the `.torrent` files will be places
`announce_url` your announce url for your tracker of choice.
`album_path` is the format of the album path. This will also have the bitrate automatically appended. See the [Moe docs](https://mrmoe.readthedocs.io/en/latest/plugins/move.html#path-configuration-options) for more information on customizing this value.

### 5. Run
`bettered -h`

## Contributing:

#### 1. Fork the repository and create a feature/bug fix branch

#### 2. Install development requirements
`$ poetry install`

#### 3. Hack away

#### 4. Lint your code
`$ pre-commit run -a`

#### 5. Submit a pull request
