"""
This is an incomplete API wrapper.
I've only implemented some of the methods that I needed to make fts.
There are other wrappers out there that you should use instead. ;)
"""

from base64 import b64decode, b64encode
from difflib import SequenceMatcher
from gzip import decompress
from os.path import basename, splitext
import hashlib
import requests
import struct, os
import xmlrpc.client
import zlib


import http.client

class ProxiedTransport(xmlrpc.client.Transport):

    def set_proxy(self, host, port=None, headers=None):
        self.proxy = host, port
        self.proxy_headers = headers

    def make_connection(self, host):
        connection = http.client.HTTPConnection(*self.proxy)
        connection.set_tunnel(host, headers=self.proxy_headers)
        self._connection = host, connection
        return connection

transport = ProxiedTransport()
transport.set_proxy('127.0.0.1', 8080)

class OpenSubtitles:
	def __init__(self):
		self.ua = "OSTestUserAgentTemp" # temp place holder. Need to register a ua with opensubs
		self.token = None
		self.proxy = xmlrpc.client.Server('https://api.opensubtitles.org/xml-rpc', transport=transport)
		# self.proxy = xmlrpc.client.Server("https://api.opensubtitles.org/xml-rpc")

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

	def download_subtitles(self, file_path, subtitle_list):
		"""
		Download and decompress a base64 encoded gzipped subtitle
		"""

		response = self.proxy.DownloadSubtitles(self.token, subtitle_list)

		if len(response['data']) > 0:
			sub_data = b64decode(response['data'][0]['data'])
			with open(file_path, 'w') as f:
				f.write(decompress(sub_data))

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

	def login(self, username="", password=""):
		"""
		Login a user to get a token
		Anonymous users are allowed but it's better to login
		for cases where there are multiple people using the API
		from the same IP (API restricitions)
		"""

		response = self.proxy.LogIn(username, password, "en", self.ua)
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

	def server_info(self):
		"""
		Get server info
		Can be used for ping or telling server info to client
		"""

		return self.proxy.ServerInfo()

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

	def try_upload_subtitle(self, filepath, subpath):
		"""
		Try to upload subtitle. Check to see if sub exists and if a movie hash exists
		"""

		movie_name = splitext(basename(filepath))[0]
		sub_name = basename(subpath)

		movie_hash, movie_size = self.get_file_data(filepath)
		with open(subpath, 'rb') as f:
			sub_content = f.read()
		sub_hash = hashlib.md5(sub_content).hexdigest()

		data = {
				"cd1" : {
					"subhash": sub_hash,
					"subfilename": sub_name,
					"moviehash": movie_hash,
					"moviebytesize": movie_size,
					"moviefilename": movie_name
				}
			}

		response = self.proxy.TryUploadSubtitles(self.token, data)
		if response['alreadyindb']:
			return (False, 'Subtitle already in database!')
		else:
			# check to see if there is an imdb match
			if len(response['data']) > 0:
				return (response['data'][0], data['cd1'])
			else:
				return (False, 'There was not a movie match in the database!')

	def upload_subtitle(self, data, subpath):
		"""
		Upload a subtitle using the information from
		the try_upload_subtitle function
		"""

		with open(subpath, 'rb') as f:
			sub_content = f.read()
		sub_hash = hashlib.md5(sub_content).hexdigest()

		data = {
			"baseinfo" : {
				"idmovieimdb": data['IDMovieImdb'],
			},
			"cd1": {
					"subhash": sub_hash,
					"subfilename": data['subfilename'],
					"moviehash": data['moviehash'],
					"moviebytesize": data['moviebytesize'],
					"moviefilename": data['moviefilename'],
					"subcontent": b64encode(sub_content).decode('utf-8')
			}
		}

		response = self.proxy.UploadSubtitles(self.token, data)
		return response['data']