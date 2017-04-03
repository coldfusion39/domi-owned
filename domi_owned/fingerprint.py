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
import requests

from .main import DomiOwned


class Fingerprint(DomiOwned):

	def fingerprint(self):
		"""
		Get information about the Domino server.
		"""
		domino_version = self.get_version()
		if domino_version:
			self.logger.info("Domino version: {0}".format(domino_version))
		else:
			self.logger.warn('Unable to identify Domino server version')

		# Get authentication type
		self.logger.info("Authentication type: {0}".format(self.auth_type.capitalize()))

		# Check URL access
		endpoints = self.check_access(self.username, self.password)
		for endpoint in endpoints:
			if endpoints[endpoint] is None:
				self.logger.warn("Could not find {0}/{1}".format(self.url, endpoint))
			elif endpoints[endpoint]:
				if self.username:
					self.logger.info("{0} has access to {1}/{2}".format(self.username, self.url, endpoint))
				else:
					self.logger.info("{0}/{1} does not require authentication".format(self.url, endpoint))
			else:
				if self.username:
					self.logger.warn("{0} does not have access to {1}/{2}".format(self.username, self.url, endpoint))
				else:
					self.logger.warn("{0}/{1} requires authentication".format(self.url, endpoint))

	def get_version(self):
		"""
		Get Domino server version.
		"""
		version_dirs = [
			'download/filesets/l_LOTUS_SCRIPT.inf',
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf',
			'api',
			'homepage.nsf',
			'help/readme.nsf?OpenAbout',
			'iNotes/Forms5.nsf',
			'iNotes/Forms6.nsf',
			'iNotes/Forms7.nsf',
			'iNotes/Forms8.nsf',
			'iNotes/Forms9.nsf'
		]

		for version_dir in version_dirs:
			try:
				response = self.session.get("{0}/{1}".format(self.url, version_dir))
			except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
				break

			if self.utilities.VERSION_REGEX.search(response.text):
				return self.utilities.VERSION_REGEX.search(response.text).group(1)

		return None
