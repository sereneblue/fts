"""
fts (findthatsub)
Instantly find subtitles via the command line

Usage:
	fts [--lang <lang>] <filepath>
	fts set <username> <password>
	fts upload <filepath> <subpath>

Options:
	-h --help                Show this screen.
	--version                Show version
	--lang=<lang>			 Specify language for subtitle. Default is 'eng'. Uses ISO 639-2 Code

Examples:
	fts The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.mp4
	fts --lang spa "The Complete Metropolis Disc 1_Title1.mp4"
	fts upload The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.mp4 The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.srt
"""

from inspect import getmembers, isclass
from docopt import docopt
from os.path import isfile, abspath

from . import __version__ as VERSION

def main():
	"""
	Main CLI entrypoint.
	"""

	from fts.fts import FTS

	f = FTS()
	options = docopt(__doc__, version=VERSION)

	if options['set']:
		f.set_credentials(options['<username>'], options['<password>'])
	if options['upload']:
		options['<filepath>'] = options['<filepath>'].replace('\\','')
		options['<subpath>'] = options['<subpath>'].replace('\\','')
		if not isfile(abspath(options['<filepath>'])) or not isfile(abspath(options['<subpath>'])):
			print('=> This is not a valid file.')
			return

		f.upload_sub(options['<filepath>'], options['<subpath>'])
	else:
		options['<filepath>'] = options['<filepath>'].replace('\\','')
		if not isfile(abspath(options['<filepath>'])):
			print('=> This is not a valid file.')
			return

		f.find_sub(options['<filepath>'], options['--lang'] if options['--lang'] else 'eng')