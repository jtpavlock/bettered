# BetterRED

## Introduction
BetterRED autmoatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

## Dependencies:
  * `mktorrent` >= 1.1
  * `ffmpeg`
  * python >= 3.6
  * pip3

## Installation:

### 1. Install python3, pip3, and ffmpeg
`$ sudo apt install python3 python3-pip ffmpeg`

### 2. Install `mktorrent`
`mktorrent` must be built from source unless your package manager includes >=v1.1

~~~
$ git clone https://github.com/Rudde/mktorrent.git
$ cd mktorrent
$ sudo make install
~~~

### 3. Clone repository and install python dependencies

~~~
$ git clone https://github.com/jtpavlock/betterRED.git
$ cd betterRED
$ pip3 install .
~~~

### 4. Configure

~~~
$ mkidr ~/.config/betterRED
$ cp betterRED/example_config.ini ~/.config/betterRED/config.ini
~~~

Edit the configuration file.

### 5. Run
`betterRED/better_red.py -h`

## Roadmap
  * Automatic recognition of flac folders that can be modified to mp3s and uploaded
  * Automatic uploading to redacted
  * 2FA support
