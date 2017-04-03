# Copyright (c) 2017, Brandan Geise [coldfusion]
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
import bs4
import re
import requests
import sys

from .utilities import Utilities

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


class DomiOwned(object):
	"""
	Core Domi-Owned functions.
	"""
	utilities = Utilities()
	logger = utilities.set_logging()

	session = requests.Session()
	session.headers = utilities.HEADERS
	session.verify = False
	session.timeout = 10

	post_data = {}

	def __init__(self, url, **kwargs):
		self.url = self.utilities.check_url(url)
		self.username = kwargs.get('username', None)
		self.password = self.utilities.parse_credentials(kwargs.get('password'))

		self.auth_type = self.get_auth(self.url)

	def get_auth(self, url):
		"""
		Determine the type of authentication the Domino web interface is using.
		"""
		try:
			response = self.session.get("{0}/names.nsf?Open".format(url))
		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			self.logger.error('Failed to establish a connection to the Domino server')
			sys.exit()

		# Basic authentication
		if response.status_code == 401 and 'www-authenticate' in response.headers:
			auth_type = 'basic'

		# Form authentication
		elif response.status_code == 200:
			if self.utilities.FORM_REGEX.search(response.text):
				auth_type = 'form'
			elif self.utilities.OPEN_REGEX.search(response.text):
				auth_type = 'open'
			else:
				self.logger.error("Unable to find {0}/names.nsf?Open".format(url))
				sys.exit()
		else:
			self.logger.error('Unable to determine authentication type')
			sys.exit()

		return auth_type

	def check_access(self, username=None, password=None):
		"""
		Check if the supplied user has access to names.nsf and webadmin.nsf.
		"""
		endpoints = {
			'names.nsf': None,
			'webadmin.nsf': None
		}

		for endpoint in endpoints:
			response = self.authenticate(username, password, endpoint)

			# Basic authentication
			if self.auth_type == 'basic':
				if response.status_code == 200:
					endpoints[endpoint] = True
				elif response.status_code == 401:
					endpoints[endpoint] = False

			# Form authentication
			elif self.auth_type == 'form':
				if response.status_code == 200:
					if endpoint == 'names.nsf':
						if self.utilities.NAMES_REGEX.search(response.text):
							endpoints[endpoint] = True
						else:
							endpoints[endpoint] = False
					else:
						if self.utilities.WEBADMIN_REGEX.search(response.text):
							endpoints[endpoint] = True
						else:
							endpoints[endpoint] = False
				else:
					if self.utilities.RESTRICTED_REGEX.search(response.text):
						endpoints[endpoint] = False

			# No authentication
			else:
				if response.status_code == 200:
					endpoints[endpoint] = True
				elif response.status_code == 404:
					endpoints[endpoint] = None
				else:
					endpoints[endpoint] = False

		return endpoints

	def authenticate(self, username, password, endpoint):
		"""
		Determine the correct authentication to use based on the Domino server's authentication type.
		"""
		if self.auth_type == 'basic' and username is not None:
			response = self.basic_auth(username, password, endpoint)
		elif self.auth_type == 'form':
			response = self.form_auth(username, password, endpoint)
		else:
			response = self.no_auth(endpoint)

		if response is None:
			self.logger.error('Failed to establish a connection to the Domino server')
			sys.exit()

		return response

	def basic_auth(self, username, password, endpoint):
		"""
		Perform Basic authentication.
		"""
		try:
			response = self.session.get("{0}/{1}".format(self.url, endpoint), auth=(username, password))
		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			return None

		return response

	def form_auth(self, username, password, endpoint):
		"""
		Perform Form authentication.
		"""
		if not self.post_data:
			try:
				response = self.session.get("{0}/names.nsf?Open".format(self.url))
			except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
				return None

			if response.status_code == 200:
				soup = bs4.BeautifulSoup((response.text).replace('\\"', '"'), 'lxml')

				# Get username and password form names
				username_field = soup.find('input', attrs={'name': self.utilities.USER_FIELD_REGEX})
				password_field = soup.find('input', attrs={'type': 'password'})
				if username_field and password_field:
					self.post_data = {
						username_field['name']: username,
						password_field['name']: password
					}
				else:
					self.post_data = {
						'Username': username,
						'Password': password
					}

				# Get redirect location
				if soup.find('input', attrs={'type': 'hidden', 'name': self.utilities.REDIRECT_FIELD_REGEX}):
					redirect_field = soup.find('input', attrs={'type': 'hidden', 'name': self.utilities.REDIRECT_FIELD_REGEX})['name']
					redirect_location = soup.find('input', attrs={'type': 'hidden', 'name': self.utilities.REDIRECT_FIELD_REGEX})['value']
					self.post_data.update({redirect_field: redirect_location})

				try:
					response = self.session.post("{0}/{1}".format(self.url, soup.find('form')['action']), data=self.post_data)
				except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
					return None

		try:
			response = self.session.get("{0}/{1}".format(self.url, endpoint))
		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			return None

		return response

	def no_auth(self, endpoint):
		"""
		No authentication request.
		"""
		try:
			response = self.session.get("{0}/{1}".format(self.url, endpoint))
		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			return None

		return response
