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
import re
import requests
from domi_owned import utility

# Get Domino version
def fingerprint(target, header):
	version_files = ['download/filesets/l_LOTUS_SCRIPT.inf', 
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf'
		]

	for version_file in version_files:
		try:
			version_url = "{0}/{1}".format(target, version_file)
			request = requests.get(version_url, headers=header, verify=False)
			if request.status_code == 200:
				version_regex = re.search("(?i)version=([0-9].[0-9].[0-9])", request.text)
				if version_regex:
					domino_version = version_regex.group(1)
					break
		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			continue

	if domino_version:
		utility.print_good("Domino version: {0}".format(version_regex.group(1)))
	else:
		utility.print_warn('Unable to fingerprint Domino version!')

# Check for access to names.nsf and webadmin.nsf
def check_portals(target, header, username, password):
	session = requests.Session()
	session.auth = (username, password)

	portals = ['names.nsf', 'webadmin.nsf']

	for portal in portals:
		try:
			portal_url = "{0}/{1}".format(target, portal)
			request = session.get(portal_url, headers=header, verify=False)
			# Handle 200 responses
			if request.status_code == 200:
				if 'form method="post"' in request.text:
					utility.print_warn("{0}/{1} requires authentication!".format(target, portal))
				elif len(username) > 0:
					utility.print_good("{0} has access to {1}/{2}".format(username, target, portal))
				else:
					utility.print_good("{0}/{1} does not require authentication".format(target, portal))
			# Handle 401 responses
			elif request.status_code == 401:
				if len(username) > 0:
					utility.print_warn("{0} does not have access to {1}/{2}!".format(username, target, portal))
				else:
					utility.print_warn("{0}/{1} requires authentication!".format(target, portal))
			# Handle all other responses
			else:
				utility.print_warn("Could not find {0}!".format(portal))
		except Exception as error:
			utility.print_error("Error: {0}".format(error))
			continue
