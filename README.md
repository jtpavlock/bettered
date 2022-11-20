# BetteRED

## Introduction
bettered automatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

bettered uses [Moe](https://github.com/MoeMusic/Moe) to initialize and read the configuration, and the plugin [moe_transcode](https://github.com/MoeMusic/moe_transcode) to handle the transcoding logic.

## Installation:

### 1. Install `bettered` from PyPI
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
redacted_announce_id = "1234abcd"
```

`transcode_path` is where the transcoded albums will be placed.
`torrent_file_path` is where the `.torrent` files will be places
`redacted_announce_id` can be found at https://redacted.ch/upload.php and is the 32 alphanumeric id in your "announce URL"

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
