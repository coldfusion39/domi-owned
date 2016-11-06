#!/usr/bin/env python
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
import os
import sys

from domi_owned import bruteforce
from domi_owned import fingerprint
from domi_owned import hashdump
from domi_owned import quickconsole
from domi_owned import utility

sys.dont_write_bytecode = True

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='domi-owned.py',
		usage='./domi-owned.py [fingerprint, hashdump, console, brute] [-h]',
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

	fingerprint_parser = subparsers.add_parser('fingerprint', help='Fingerprint Domino server', usage='./domi-owned.py fingerprint URL --username USERNAME --password PASSWORD')
	fingerprint_parser.add_argument('url', help='Domino server URL')
	fingerprint_parser.add_argument('--username', help='Username', default='', required=False)
	fingerprint_parser.add_argument('--password', help='Password', default='', nargs='+', required=False)

	dump_parser = subparsers.add_parser('hashdump', help='Dump Domino hashes', usage='./domi-owned.py hashdump URL --username USERNAME --password PASSWORD')
	dump_parser.add_argument('url', help='Domino server URL')
	dump_parser.add_argument('--username', help='Username', default='', required=False)
	dump_parser.add_argument('--password', help='Password', default='', nargs='+', required=False)

	console_parser = subparsers.add_parser('console', help='Interact with Domino Quick Console', usage='./domi-owned.py console URL --username USERNAME --password PASSWORD')
	console_parser.add_argument('url', help='Domino server URL')
	console_parser.add_argument('--username', help='Username', default='', required=False)
	console_parser.add_argument('--password', help='Password', default='', nargs='+', required=False)

	brute_parser = subparsers.add_parser('brute', help='Reverse brute force Domino server', usage='./domi-owned.py brute URL USERLIST --password PASSWORD')
	brute_parser.add_argument('url', help='Domino server URL')
	brute_parser.add_argument('userlist', help='List of usernames')
	brute_parser.add_argument('--password', help='Password', default='', nargs='+', required=False)

	args = parser.parse_args()

	# Process Domino URL
	target = utility.check_url(args.url)
	if target:
		# Detect type of authentication
		auth_type = utility.detect_auth(target)

		# Fingerprint
		if args.action == 'fingerprint':
			utility.print_status('Fingerprinting Domino server')
			fingerprint.fingerprint(target, args.username, ' '.join(args.password), auth_type)

		# Dump hashes
		elif args.action == 'hashdump':
			utility.print_status('Dumping account hashes')
			hashdump.enum_accounts(target, args.username, ' '.join(args.password), auth_type)

		# Interact with Quick Console
		elif args.action == 'console':
			utility.print_status('Accessing Domino Quick Console')
			quickconsole.check_access(target, args.username, ' '.join(args.password), auth_type)

		# Reverse brute force
		elif args.action == 'brute':
			if os.path.isfile(args.userlist):
				utility.print_status("Starting reverse brute force with '{0}' as the password".format(' '.join(args.password)))
				bruteforce.reverse_bruteforce(target, os.path.abspath(args.userlist), ' '.join(args.password), auth_type)
			else:
				utility.print_warn('You must supply a file containing a list of usernames')

	else:
		utility.print_warn('Invalid URL provided')
