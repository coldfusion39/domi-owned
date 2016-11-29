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
		version_regex = re.compile(r'(?:version|domino administrator|domino|release)[=":\s]{0,4}([\d.]+)(?:\s|\")?', re.I)

		version_files = [
			'download/filesets/l_LOTUS_SCRIPT.inf',
			'download/filesets/n_LOTUS_SCRIPT.inf',
			'download/filesets/l_SEARCH.inf',
			'download/filesets/n_SEARCH.inf',
			'api',
			'homepage.nsf',
			'help/readme.nsf?OpenAbout',
			'iNotes/Forms5.nsf',
			'iNotes/Forms6.nsf',
			'iNotes/Forms7.nsf',
			'iNotes/Forms8.nsf'
		]

		for version_file in version_files:
			try:
				response = requests.get(
					"{0}/{1}".format(self.domiowned.url, version_file),
					headers=self.domiowned.HEADERS,
					timeout=10,
					verify=False
				)

				if version_regex.search(response.text):
					self.domino_version = version_regex.search(response.text).group(1)
					break

			except requests.exceptions.RequestException as error:
				break

		return self.domino_version
