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
import fake_useragent
import os
import sys

from domi_owned import fingerprint
from domi_owned import hashdump
from domi_owned import quickconsole
from domi_owned import utility

sys.dont_write_bytecode = True

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
	parser.add_argument('--url', help='Domino server URL', required=True)
	parser.add_argument('-u', '--username', help='Username', default='', required=False)
	parser.add_argument('-p', '--password', help='Password', default='', nargs='+', required=False)
	parser.add_argument('--hashdump', help='Dump Domino hashes', action='store_true', required=False)
	parser.add_argument('--quickconsole', help='Interact with Domino Quick Console', action='store_true', required=False)
	args = parser.parse_args()

	# Process Domino URL
	target = utility.process_url(args.url)
	if target == None:
		utility.print_warn('Please provide a valid URL!')
		sys.exit(0)

	# Setup headers
	user_agent = fake_useragent.UserAgent()
	header = {
		'User-Agent': user_agent.random,
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Connection': 'keep-alive'
	}

	# Interact with quick console
	if args.quickconsole:
		utility.print_status('Accessing Domino Quick Console...')
		quickconsole.check_access(target, header, args.username, ' '.join(args.password))

	# Dump hashes
	elif args.hashdump:
		utility.print_status('Enumerating accounts...')
		hashdump.enum_accounts(target, header, args.username, ' '.join(args.password))

	# Fingerprint
	else:
		utility.print_status('Fingerprinting Domino server...')
		fingerprint.fingerprint(target, header)
		fingerprint.check_portals(target, header, args.username, ' '.join(args.password))
