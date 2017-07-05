from difflib import SequenceMatcher
from io import BytesIO
from os.path import basename, splitext, abspath, expanduser
from .opensubs import OpenSubtitles
from urllib.parse import quote
from zipfile import ZipFile
import re
import requests

class FTS:
	def __init__(self):
		self.session = requests.session()
		self.session.headers.update({
				'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
			})
		self.langages = {
			"ara":"Arabic",
			"eng":"English",
			"dan":"Danish",
			"dut":"Dutch",
			"fin":"Finnish",
			"fre":"French",
			"heb":"Hebrew",
			"ind":"Indonesian",
			"ita":"Italian",
			"may":"Malay",
			"nor":"Norwegian",
			"per":"Farsi/Persian",
			"por":"Brazillian Portuguese",
			"rum":"Romanian",
			"spa":"Spanish",
			"swe":"Swedish",
			"vie":"Vietnamese"
		}
		self.opensubs = OpenSubtitles()

	def check_credentials(self):
		"""
		Check for valid credentials and token for a user account
		"""

		try:
			with open(expanduser('~/.fts')) as f:
				user, password = f.read().split('\n')
			if not self.opensubs.login(user, password):
				print('Credentials are not valid! Using anonymous login...')
				raise ValueError
		except ValueError:
			# Use anonymous login if no account provided
			self.opensubs.login()

	def set_credentials(self, username, password):
		"""
		Save valid credentials and token for future use
		"""

		if self.opensubs.login(username, password):
			with open(expanduser('~/.fts'), 'w') as f:
				f.write("{}\n{}".format(username, password))
			print('Credentials saved')
			return
		print('Credentials are not valid')

	def find_sub(self, fn, lang):
		"""
		Check OpenSubtitles first, then fallback to subscene
		"""

		self.check_credentials()

		# opensubtitles uses "pob" instead f "por" for Portuguese
		if self.check_opensubs(fn, lang if lang != "por" else "pob"):
			self.opensubs.logout()
			return
		print('Can\'t find subtitle on OpenSubtitles. Checking subscene...')
		if self.check_subscene(fn, lang):
			return
		print('Couldn\'t find subtitle on subscene either. :\'(')

	def check_opensubs(self, file, lang):
		"""
		Check OpenSubtitles for the subtitle
		"""

		# check movie hash & size for a subtitle
		mdata = self.opensubs.get_file_data(file)

		filename = splitext(basename(file))[0]
		response = self.opensubs.search_subtitles(lang, movie_hash=mdata[0], movie_size=mdata[1])

		if response:
			# get the full path of the video without the extensions
			file_path = splitext(abspath(file))[0]

			# get the subtile ext from the api response
			file_path += ("." + response['data'][0]['SubFileName'].split('.')[-1])

			# Might get the same size & hash for different movies. :o
			# Going to use ratios to filter out the noise here :)
			weights = [SequenceMatcher(None, filename, i['SubFileName']).quick_ratio() for i in response['data']]

			if max(weights) > .6:
				option = weights.index(max(weights))
				print('Found subtitle! Downloading...')
				self.opensubs.download(file_path, response['data'][option]['SubDownloadLink'])
				print('Subtitle downloaded to:\n{}'.format(file_path))
				return True

		# if above fails, check by filename
		data = self.opensubs.guess_movie(filename)
		if data:
			response = self.opensubs.search_subtitles(lang, imdbid=data)
			if response:
				print('Found subtitle! Downloading...')
				# get the full path of the video without the extensions
				file_path = splitext(abspath(file))[0]

				# get the subtile ext from the api response
				file_path += ("." + response['data'][0]['SubFileName'].split('.')[-1])

				self.opensubs.download(file_path, response['data'][0]['SubDownloadLink'])
				print('Subtitle downloaded to:\n{}'.format(file_path))
				return True
		return False

	def check_subscene(self, filepath, lang="eng"):
		"""
		Check subscene for the subtitle
		Have to parse manually since they don't have an API
		"""

		# get the id for the language and insert the cookie into the session
		# and set the language filter in the cookie
		response = self.session.get('https://u.subscene.com/filter').text
		lang_id = re.search('value="(\d+)" type="checkbox".*?>.*?{}'.format(self.langages[lang]), response).groups()[0]
		self.session.cookies.set('LanguageFilter', lang_id, domain='.subscene.com', path='/')

		# find list of subtitles and compared to filename
		filename = splitext(basename(filepath))[0]
		response = self.session.get("https://subscene.com/subtitles/release?q={}&r=true".format(quote(filename))).text
		subs = re.findall('href="(\/subtitles\/.*?)">\s*<span.*?>\s*{}\s*.*?<\/span>\s*<span>\s*(.*?)\s*<\/span>'\
				.format(self.langages[lang]), response)

		if len(subs) > 0:
			# Stumbled upon difflib while looking around for fuzzy search in python
			# That's quite a nice hidden gem in the python std lib. :D
			# get list of weights (filename compared to subtitle movie filename)
			weights = [SequenceMatcher(None, filename, i[1]).quick_ratio() for i in subs]

			# find max, that should be the best match
			option = weights.index(max(weights))

			if weights[option] > .75:
				print('Found subtitle (subscene): {}'.format(subs[option][1]))
				response = self.session.get("https://subscene.com" + subs[option][0]).text
				download_link = re.search('href="(/subtitle/download\?mac=.*?)"', response).groups()[0]

				# download sub to memory
				r = self.session.get("https://subscene.com" + download_link, stream=True)
				z = ZipFile(BytesIO(r.content))

				# get the subtile ext from the zip file
				file_path = splitext(abspath(filepath))[0]
				file_path += ("." + z.namelist()[0].split('.')[-1])

				try:
					# save subtitle (utf-8)
					with open(file_path, 'w') as f:
						f.write(z.read(z.namelist()[0]).decode('utf-8'))
				except UnicodeDecodeError:
					# char encoding is not utf-8
					try:
						with open(file_path, 'w') as f:
							f.write(z.read(z.namelist()[0]).decode('iso-8859-1'))
					except UnicodeDecodeError:
						with open(file_path, 'w') as f:
							f.write(z.read(z.namelist()[0]).decode('latin-1'))
				print('Subtitle downloaded to:\n{}'.format(file_path))
				return True
		return False
