#!/usr/bin/env python3
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
import argparse

from domi_owned.bruteforce import BruteForce
from domi_owned.enumerate import Enumerate
from domi_owned.fingerprint import Fingerprint
from domi_owned.hashdump import HashDump
from domi_owned.quickconsole import QuickConsole
from domi_owned.utilities import Banner


def main():
	parser = argparse.ArgumentParser(usage='./domi-owned.py [fingerprint, enumerate, bruteforce, hashdump, quickconsole] [-h]', formatter_class=argparse.RawDescriptionHelpFormatter, description=(Banner.SHOW))
	subparsers = parser.add_subparsers(dest='action', help='Action to perform on IBM/Lotus Domino server')

	fingerprint_parser = subparsers.add_parser('fingerprint', help='Fingerprint the Domino server', usage='./domi-owned.py fingerprint URL --username USERNAME --password PASSWORD')
	fingerprint_parser.add_argument('url', help='Domino server URL')
	fingerprint_parser.add_argument('--username', help='Username', default=None)
	fingerprint_parser.add_argument('--password', help='Password', default=None)

	enum_parser = subparsers.add_parser('enumerate', help='Enumerate Domino files and directories', usage='./domi-owned.py enumerate URL --username USERNAME --password PASSWORD --wordlist WORDLIST')
	enum_parser.add_argument('url', help='Domino server URL')
	enum_parser.add_argument('--wordlist', help='Wordlist containing Domino files and directories', default=None)
	enum_parser.add_argument('--username', help='Username', default=None)
	enum_parser.add_argument('--password', help='Password', default=None)

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

	# Fingerprint
	if args.action == 'fingerprint':
		print_status('Fingerprinting Domino server')
		domino = Fingerprint(args.url, username=args.username, password=args.password)
		domino.fingerprint()

	# Enumerate
	elif args.action == 'enumerate':
		print_status('Enumerating Domino URLs')
		domino = Enumerate(args.url, username=args.username, password=args.password)
		domino.enumerate(args.wordlist)

	# Brute force
	elif args.action == 'bruteforce':
		if args.password:
			print_status("Starting reverse brute force with '{0}' as the password".format(args.password))
		else:
			print_status('Starting reverse brute force with username as password')

		domino = BruteForce(args.url, password=args.password)
		domino.bruteforce(args.userlist)

	# Hash dump
	elif args.action == 'hashdump':
		print_status('Dumping Domino account hashes')
		domino = HashDump(args.url, username=args.username, password=args.password)
		domino.dump()

	# Quick Console
	elif args.action == 'quickconsole':
		print_status('Accessing Domino Quick Console')
		domino = QuickConsole(args.url, username=args.username, password=args.password)
		domino.quickconsole()

	# No actions given, print help
	else:
		parser.print_help()


def print_status(message):
	print("\033[1m\033[34m[*]\033[0m {0}".format(message))


if __name__ == '__main__':
	main()
