"""
This is an incomplete API wrapper.
I've only implemented some of the methods that I needed to make fts.
There are other wrappers out there that you should use instead. ;)
"""

from base64 import b64decode
from difflib import SequenceMatcher
from gzip import decompress
import requests
import struct, os
import xmlrpc.client
import zlib

class OpenSubtitles:
	def __init__(self):
		self.ua = "OSTestUserAgentTemp" # temp place holder. Need to register a ua with opensubs
		self.token = None
		self.proxy = xmlrpc.client.Server("https://api.opensubtitles.org/xml-rpc")

	def download_subtitles(self, file_path, subtitle_list):
		"""
		Download and decompress a base64 encoded gzipped subtitle
		"""

		response = self.proxy.DownloadSubtitles(self.token, subtitle_list)

		if len(response['data']) > 0:
			sub_data = b64decode(response['data'][0]['data'])
			with open(file_path, 'w') as f:
				f.write(decompress(sub_data))

	def download(self, file_path, gzip_link):
		"""
		Download and decompress from the gz link.
		Saves an extra API call
		"""

		r = requests.get(gzip_link, headers={'User-Agent': self.ua}, stream=True)
		sub = zlib.decompress(r.content, 16+zlib.MAX_WBITS)

		try:
			with open(file_path, 'w') as f:
				f.write(sub.decode('iso-8859-1'))
		except UnicodeDecodeError:
			try:
				with open(file_path, 'w') as f:
					f.write(sub.decode('iso-8859-1'))
			except UnicodeDecodeError:
				with open(file_path, 'w') as f:
					f.write(sub.decode('latin-1'))

	def guess_movie(self, movie):
		"""
		Guess movie from string
		"""

		response = self.proxy.GuessMovieFromString(self.token, [movie])
		guesses = response['data'][movie]['GuessMovieFromString']

		# check if there was a guess
		if len(guesses) > 0:
			weights = [SequenceMatcher(None, movie, i['MovieName']).quick_ratio() for i in guesses]
			# check if any weights are over .8
			if max(weights) > .8:
				return int(guess_keys[guess_keys.index(max(weights))]['IDMovieIMDB'])
		return False

	def server_info(self):
		"""
		Get server info
		Can be used for ping or telling server info to client
		"""

		return self.proxy.ServerInfo()

	def login(self, username="", password="", lang="en", ua=""):
		"""
		Login a user to get a token
		Anonymous users are allowed but it's better to login
		for cases where there are multiple people using the API
		from the same IP (API restricitions)
		"""

		ua = ua if ua else self.ua
		response = self.proxy.LogIn(username, password, lang, ua)
		if response['status'] == "401 Unauthorized":
			# opensubs returns a token that we can use even if we don't have correct credentials
			# that's nice of them :)
			return False
		if response.get('token', None):
			self.token = response['token']
			return self.token
		return False

	def logout(self):
		"""
		Logout a user, ends their session.
		"""

		if self.token:
			self.proxy.LogOut(self.token)

	def search_subtitles(self, sub_lang, movie_hash="", movie_size=0, imdbid=0, query=0, season=0, ep_num=0, tags="", limit=10):
		"""
		Search subtitles via several parameters: movie hash, imdbid, or query
		"""

		data = [{}]

		if movie_hash:
			data[0]['moviehash'] = movie_hash
			data[0]['moviebytesize'] = movie_size
		elif imdbid:
			data[0]['imdbid'] = imdbid
		elif query:
			data[0]['query'] = query

		if season:
			data[0]['season'] = season
			if episode:
				data[0]['episode_num'] = ep_num
		if tags:
			data[0]['tags'] = tags

		data[0]['sublanguageid'] = sub_lang
		data[0]['limit'] = limit

		response = self.proxy.SearchSubtitles(self.token, data)

		if len(response['data']) > 0:
			return response
		return False

	def get_file_data(self, file_path):
		"""
		Check the file hash and size. Pretty nifty feature to get the most accurate subtitle.
		Courtesy of OpenSubtitles: http://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
		"""

		try:
			longlongformat = '<q'  # little-endian long long
			bytesize = struct.calcsize(longlongformat)

			f = open(file_path, "rb")

			filesize = os.path.getsize(file_path)
			hash = filesize

			if filesize < 65536 * 2:
				return False

			for x in range(int(65536/bytesize)):
				buffer = f.read(bytesize)
				(l_value,)= struct.unpack(longlongformat, buffer)
				hash += l_value
				hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number


			f.seek(max(0,filesize-65536),0)
			for x in range(int(65536/bytesize)):
				buffer = f.read(bytesize)
				(l_value,)= struct.unpack(longlongformat, buffer)
				hash += l_value
				hash = hash & 0xFFFFFFFFFFFFFFFF

			f.close()
			# convert filesize int to string due to xml-rpc limits with int size.
			return  ("%016x" % hash, str(filesize))
		except IOError:
			return False
