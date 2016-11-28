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

from .helpers import Helpers


class QuickConsole(cmd.Cmd, object):
	"""Interact with Domino Quick Console through web requests"""

	def __init__(self, domiowned, info, username, password):
		cmd.Cmd.__init__(self)
		self.util = Helpers()
		self.domiowned = domiowned
		self.info = info
		self.username = username
		self.password = password
		self.operator = '> '

		if self.info['os'] == 'windows':
			self.prompt = "{0}:\\Windows\\System32>".format(self.info['path'].split(':')[0])
		else:
			self.prompt = "{0}@{1}:/local/notesdata$ ".format(self.info['user'], self.info['hostname'])

	def emptyline(self):
		pass

	def default(self, line):
		self.interact(line)

	def interact(self, command):
		response = self.domiowned._send_command(self.info['os'], self.info['path'], self.operator, command, self.username, self.password)
		if response.status_code == 200 and '>' in self.operator:
			print(response.text)
		elif response.status_code == 200 and '>' not in self.operator:
			self.util.print_warn('Unable to delete outfile')
		elif response.status_code == 404 and '>' not in self.operator:
			self.util.print_good('Outfile successfully deleted')
		else:
			self.util.print_warn('Outfile not found')
			self.do_exit

	def do_EOF(self, line):
		self.operator = ''
		if self.info['os'] == 'windows':
			command = 'del'
		else:
			command = 'rm'

		self.interact(command)

		return True

	def help_EOF(self):
		print('Type exit to quit')

	do_exit = do_EOF
	help_exit = help_EOF
