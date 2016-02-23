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
import re
import requests

from domi_owned import utility

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass

# Get Domino version
def fingerprint(target, username, password, auth):
	domino_version = None

	version_files = ['download/filesets/l_LOTUS_SCRIPT.inf', 
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf',
			'api',
			'homepage.nsf',
			'help/readme.nsf'
		]

	for version_file in version_files:
		try:
			version_url = "{0}/{1}".format(target, version_file)
			request = requests.get(version_url, headers=utility.get_headers(), timeout=5, allow_redirects=False, verify=False)
			if request.status_code == 200:
				version_regex = re.compile('(version=|version\":\"|domino administrator |domino |release )([0-9.]{1,7})(\s|\")', re.I)
				if version_regex.search(request.text):
					domino_version = version_regex.search(request.text).group(2)
					break
		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			continue

	if domino_version:
		utility.print_good("Domino version: {0}".format(domino_version))
	else:
		utility.print_warn('Unable to fingerprint Domino version!')

	check_portals(target, username, password, auth)

# Check for access to names.nsf and webadmin.nsf
def check_portals(target, username, password, auth):
	portals = ['names.nsf', 'webadmin.nsf']

	for portal in portals:
		portal_url = "{0}/{1}".format(target, portal)
		try:
			# Page not eternally accessible
			if auth == None:
				utility.print_warn("Could not find {0}!".format(portal))

			# Basic authentication
			elif auth == 'basic':
				if len(username) > 0:
					access = utility.basic_auth(portal_url, username, password)
					if access:
						utility.print_good("{0} has access to {1}".format(username, portal_url))
					else:
						utility.print_warn("{0} does not have access to {1}".format(username, portal_url))
				else:
					utility.print_warn("{0} requires authentication!".format(portal_url))

			# Form authentication
			elif auth == 'form':
				if len(username) > 0:
					access, session = utility.form_auth(portal_url, username, password)
					if access:
						utility.print_good("{0} has access to {1}".format(username, portal_url))
					else:
						utility.print_warn("{0} does not have access to {1}".format(username, portal_url))
				else:
					utility.print_warn("{0} requires authentication!".format(portal_url))

			# Page does not require authentication
			else:
				utility.print_good("{0} does not require authentication".format(portal_url))

		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			continue
