# BetteRED

## Introduction
bettered automatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

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

### 4. Configure (Alternative configuration file locations can be specified with the -c commandline option)

~~~
$ mkdir -p ~/.config/bettered/
$ cp example_config.ini ~/.config/bettered/config.ini
~~~

Edit the configuration file.

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
