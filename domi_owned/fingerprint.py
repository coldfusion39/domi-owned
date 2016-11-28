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

from requests.exceptions import ConnectionError

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


class Fingerprint(object):
	"""Get information about the Domino server"""

	def __init__(self, domiowned):
		self.domiowned = domiowned

		self.domino_version = None

	# Get Domino version
	def get_version(self):
		version_regex = re.compile(r'(version=|version\":\"|domino administrator |domino |release )([0-9.]{1,7})(\s|\")', re.I)

		version_files = [
			'download/filesets/l_LOTUS_SCRIPT.inf',
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf',
			'api',
			'homepage.nsf',
			'help/readme.nsf'
		]

		for version_file in version_files:
			try:
				response = requests.get(
					"{0}/{1}".format(self.domiowned.url, version_file),
					headers=self.domiowned.HEADERS,
					allow_redirects=False,
					timeout=5,
					verify=False
				)

				if response.status_code == 200 and version_regex.search(response.text):
					self.domino_version = version_regex.search(response.text).group(2)
					break

			except ConnectionError as error:
				break

		return self.domino_version
