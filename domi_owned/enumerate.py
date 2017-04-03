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
import aiohttp
import asyncio
import itertools
import signal
import sys
import os

from .main import DomiOwned


class Enumerate(DomiOwned):

	def enumerate(self, directories):
		"""
		Enumerate common Domino server URLs.
		"""
		self.check_access(self.username, self.password)

		# Build directory list
		urls = self.build_directories(directories)

		self.enum_dirs(urls)

	def build_directories(self, directories):
		"""
		Create list of Domino URLs to enumerate.
		"""
		urls = []

		# Use the supplied Domino directory list
		if directories is None:
			endpoints = open(os.path.abspath('./domi_owned/data/domino_endpoints.txt'), 'r').readlines()
			dirs = open(os.path.abspath('./domi_owned/data/domino_dirs.txt'), 'r').readlines()

			for endpoint in endpoints:
				urls.append("{0}/{1}".format(self.url, endpoint.rstrip()))

			for combined_dir in list(itertools.product(dirs, endpoints)):
				urls.append("{0}/{1}{2}".format(self.url, combined_dir[0].rstrip(), combined_dir[1].rstrip()))

		# Use the user supplied Domino directory list
		else:
			dirs = open(os.path.abspath(directories), 'r')
			for combined_dir in dirs:
				urls.append("{0}/{1}".format(self.url, combined_dir.lstrip('/').rstrip()))

		return urls

	def signal_handler(self):
		"""
		Gracefully handle exiting enumeration.
		"""
		self.logger.debug('Got Ctrl-C, stopping all tasks...')
		for task in asyncio.Task.all_tasks():
			task.cancel()

	def enum_dirs(self, urls):
		"""
		Create client session based on authentication type.
		"""
		loop = asyncio.get_event_loop()
		loop.add_signal_handler(signal.SIGINT, self.signal_handler)

		if self.username and self.auth_type == 'basic':
			client = aiohttp.ClientSession(headers=self.utilities.HEADERS, auth=aiohttp.BasicAuth(self.username, self.password), loop=loop)

		elif self.auth_type == 'form':
			# Check if cookies or SSO are being used for authentication
			if 'DomAuthSessId' in self.session.cookies:
				session_id = dict(DomAuthSessId=self.session.cookies['DomAuthSessId'])
			elif 'LtpaToken' in self.session.cookies:
				session_id = dict(LtpaToken=self.session.cookies['LtpaToken'])
			else:
				session_id = None

			client = aiohttp.ClientSession(headers=self.utilities.HEADERS, cookies=session_id, loop=loop)

		else:
			client = aiohttp.ClientSession(headers=self.utilities.HEADERS, loop=loop)

		with client as session:
			try:
				loop.run_until_complete(self.query(session, urls))
			except asyncio.CancelledError:
				sys.exit()
			except Exception as error:
				self.logger.error('An error occurred while enumerating Domino URLs')
				sys.exit()

	async def query(self, session, urls):
		"""
		Build asynchronous requests.
		"""
		await asyncio.gather(*[self.get(session, url) for url in urls])

	async def get(self, session, url):
		"""
		Request account URL and parse response.
		"""
		async with session.get(url, compress=True) as response:
			if self.auth_type == 'form' and self.utilities.FORM_REGEX.search(await response.text()):
				return

			if response.status == 200:
				self.logger.info("200 - {0}".format(url))
			elif response.status == 401:
				self.logger.warning("401 - {0}".format(url))
			else:
				return
