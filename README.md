# fts (findthatsub)
Instantly find subtitles via the command line

fts will have difficulties finding subtitles for obscure media content but most recent releases should be covered by the services that it uses to find subtitles, [OpenSubtitles](https://opensubtitles.org/) and [Subscene](https://subscene.com/).

# Install

### Using pip

```
$ pip install fts
```

### Build from source

```
$ git clone https://github.com/sereneblue/fts
$ cd fts
$ python setup.py install
```

# Usage

	fts [--lang <lang>] <filepath>
	fts set <username> <password>
	fts upload <filepath> <subpath>

### Options

	-h --help                Show this screen.
	--version                Show version
	--lang=<lang>			 Specify language for subtitle. Default is 'eng'. Uses ISO 639-2 code

### Example

	$ fts The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.mp4
    Found subtitle! Downloading...
    => Subtitle downloaded to:
	/home/sereneblue/Downloads/The Pirate Bay Away From Keyboard (2013 [1080p]/The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.srt

	$ fts --lang spa "The Complete Metropolis Disc 1_Title1.mp4"
	Can't find subtitle on OpenSubtitles. Checking subscene...
	=> Couldn't find subtitle on subscene either. :'(

	$ fts upload The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.mp4 The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.srt
	=> Subtitle already in database!

### Use your OpenSubtitles account

It is strongly recommended that you create an OpenSubtitles account for use with this tool. Once your account is activated, store your credentials by running:

```
$ fts set user pass
```

Or create a file at '~/.ftsrc' like this:

	user
	pass

# Thanks

Please consider supporting [OpenSubtitles](https://www.opensubtitles.org/en/support#vip) & [Subscene](https://subscene.com) (by viewing their ads)