# BetteRED

## Introduction
bettered automatically transcodes a given path of flac files to mp3 files
based on desired quality (MP3 V0 or MP3 320). It will then create a
corresponding torrent file to be uploaded to redacted.

## Dependencies:
  * `mktorrent` >= 1.1
  * `lame`
  * `flac`
  * python >= 3.6
  * pip3

## Installation:

### 1. Install python3, pip3, flac, and lame
`$ sudo apt install python3 python3-pip lame flac`

### 2. Install `mktorrent`
`mktorrent` must be built from source unless your package manager includes >=v1.1

~~~
$ git clone https://github.com/Rudde/mktorrent.git
$ cd mktorrent
$ sudo make install
~~~

### 3. Clone repository and install python dependencies

~~~
$ git clone https://github.com/jtpavlock/bettered.git
$ cd bettered
$ python3 -m pip install .
~~~

### 4. Configure (Alternative configuration file locations can be specified with the -c commandline option)

~~~
$ mkdir -p ~/.config/bettered/
$ cp example_config.ini ~/.config/bettered/config.ini
~~~

Edit the configuration file.

### 5. Run
`bettered -h`

If this doesn't work, make sure that ~/.local/bin is in your path, or simply run:

`~/.local/bin/bettered -h`

## Roadmap
  * Support flac24bit -> flac transcodes
  
*I currently have no plans to integrate any automatic workflow into redacted.
## Development:

#### 1. Fork the repository and create a feature/bug fix branch

#### 2. Install development requirements
`$ python3 -m pip install -e . ".[dev]"`

#### 3. Hack away
#### 4. Create some tests

#### 5. Make sure it's good code
`$ pytest --cov bettered test/`

`$ pylint`

#### 6. Submit a pull request
