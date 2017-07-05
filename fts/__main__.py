"""
fts (findthatsub)
Instantly find subtitles via the command line

Usage:
	fts [--lang <lang>] <filepath>
	fts set <username> <password>

Options:
	-h --help                Show this screen.
	--version                Show version
	--lang=<lang>			 Specify language for subtitle. Default is 'eng'. Uses ISO 639-2 Code

Examples:
	fts The.Pirate.Bay.Away.From.Keyboard.2013.1080p.BRrip.x264.GAZ.YIFY.mp4
	fts --lang spa "The Complete Metropolis Disc 1_Title1.mp4"
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
	else:
		#check if valid file
		if not isfile(abspath(options['<filepath>'].replace('\\',''))):
			print('This is not a valid file.')
			return

		# remove \\ from file path if spaces in filename
		f.find_sub(options['<filepath>'].replace('\\',''), options['--lang'] if options['--lang'] else 'eng')
