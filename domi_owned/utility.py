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
import re
import requests
from bs4 import BeautifulSoup

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


# Check for valid URL
def check_url(url):
	url_regex = re.compile('https?://[a-z0-9\-.:]+', re.I)
	if url_regex.search(url):
		target = url_regex.search(url).group(0)
	else:
		target = None

	return target


# Generate user agent
def get_headers():
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Connection': 'keep-alive'
	}

	return headers


# Determine what type of authentication the Domino server is using
def detect_auth(target):
	url = "{0}/names.nsf".format(target)
	request = requests.get(url, headers=get_headers(), allow_redirects=False, verify=False)

	# Basic authentication
	if request.status_code == 401 and 'www-authenticate' in request.headers:
		auth_type = 'basic'

	# Form authentication
	elif request.status_code == 200:
		post_regex = re.compile('method=\'post\'|method=\"post\"|method=post', re.I)
		notes_regex = re.compile('name=\'NotesView\'|name=\"NotesView\"|name=NotesView', re.I)
		if post_regex.search(request.text):
			auth_type = 'form'
		elif notes_regex.search(request.text):
			auth_type = 'open'
		else:
			auth_type = 'form'

	# Unable to access web login
	elif request.status_code > 401:
		auth_type = None

	# Other types (default to basic)
	else:
		auth_type = 'basic'

	return auth_type


# Basic authentication
def basic_auth(target, username, password):
	basic_request = requests.get(target, headers=get_headers(), auth=(username, password), verify=False)

	if 'names.nsf' in target:
		notes_regex = re.compile('name=\'NotesView\'|name=\"NotesView\"|name=NotesView', re.I)
		if basic_request.status_code == 200 and notes_regex.search(basic_request.text):
			return True
		else:
			return False
	else:
		if basic_request.status_code == 200:
			return True
		else:
			return False


# Form authentication
def form_auth(target, username, password):
	with requests.Session() as session:
		initial_request = session.get(target, headers=get_headers(), verify=False)
		if initial_request.status_code == 200:
			origional_content = initial_request.headers['content-length']
			soup = BeautifulSoup(initial_request.text, 'lxml')

			# Get location to send POST
			post_directory = soup.find('form')['action']
			post_url = "{0}{1}".format(target, post_directory)

			# Get username form name
			username_field = soup.find('input', attrs={'type': 'text'})['name']

			# Get password form name
			password_field = soup.find('input', attrs={'type': 'password'})['name']

			data = {
				username_field: username,
				password_field: password
			}

			# Get redirect form name and location
			if soup.find('input', attrs={'type': 'hidden'})['name']:
				redirect_field = soup.find('input', attrs={'type': 'hidden'})['name']
				redirect_location = soup.find('input', attrs={'type': 'hidden'})['value']
				data.update({redirect_field: redirect_location})

			# Try authenticating
			form_request = session.post(post_url, headers=get_headers(), data=data, verify=False)
			if 'names.nsf' in target:
				notes_regex = re.compile('name=\'NotesView\'|name=\"NotesView\"|name=NotesView', re.I)

				if notes_regex.search(form_request.text) and session.cookies['DomAuthSessId']:
					return True, session
				else:
					return False, None
			else:
				webadmin_regex = re.compile('<title>.*Administration</title>', re.I)
				if webadmin_regex.search(form_request.text) and session.cookies['DomAuthSessId']:
					return True, session
				else:
					return False, None


# Colored print messages
def print_error(msg):
	print "\033[1m\033[31m[-]\033[0m {0}".format(msg)


def print_status(msg):
	print "\033[1m\033[34m[*]\033[0m {0}".format(msg)


def print_good(msg):
	print "\033[1m\033[32m[+]\033[0m {0}".format(msg)


def print_warn(msg):
	print "\033[1m\033[33m[!]\033[0m {0}".format(msg)
