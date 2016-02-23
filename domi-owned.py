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
import os
import sys

from domi_owned import fingerprint
from domi_owned import hashdump
from domi_owned import quickconsole
from domi_owned import bruteforce
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
	parser.add_argument('url', help='Domino server URL')
	parser.add_argument('-u', help='Username or list of usernames', dest='username', default='', required=False)
	parser.add_argument('-p', help='Password', dest='password', default='', nargs='+', required=False)
	parser.add_argument('--hashdump', help='Dump Domino hashes', action='store_true', required=False)
	parser.add_argument('--quickconsole', help='Interact with Domino Quick Console', action='store_true', required=False)
	parser.add_argument('--bruteforce', help='Reverse brute force Domino server', action='store_true', required=False)
	args = parser.parse_args()

	# Process Domino URL
	target = utility.check_url(args.url)
	if target == None:
		utility.print_warn('Please provide a valid URL!')
	else:

		# Detect type of authentication the Domino server is using
		auth_type = utility.detect_auth(target)

		# Interact with quick console
		if args.quickconsole:
			utility.print_status('Accessing Domino Quick Console...')
			quickconsole.check_access(target, args.username, ' '.join(args.password), auth_type)

		# Dump hashes
		elif args.hashdump:
			utility.print_status('Dumping account hashes...')
			hashdump.enum_accounts(target, args.username, ' '.join(args.password), auth_type)

		# Reverse brute force
		elif args.bruteforce:
			if os.path.isfile(args.username):
				utility.print_status("Starting reverse brute force with {0} as the password...".format(' '.join(args.password)))
				bruteforce.reverse_bruteforce(target, args.username, ' '.join(args.password), auth_type)
			else:
				utility.print_warn('You must supply the full path to a file containing a list of usernames!')

		# Fingerprint
		else:
			utility.print_status('Fingerprinting Domino server...')
			fingerprint.fingerprint(target, args.username, ' '.join(args.password), auth_type)
