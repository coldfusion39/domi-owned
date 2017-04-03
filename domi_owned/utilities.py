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
import logging.handlers
import re
import sys
import tqdm


class Utilities(object):
	"""
	Utility functions.
	"""
	HEADERS = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Connection': 'close'
	}

	URL_REGEX = re.compile(r'(https?:\/\/[\d\w.:-]+)', re.I)
	FORM_REGEX = re.compile(r'method[\'\"= ]{1,4}post[\'\"]?', re.I)
	OPEN_REGEX = re.compile(r'name[\'\"= ]{1,4}notesview[\'\"]?', re.I)
	ACCOUNT_REGEX = re.compile(r'/([a-f0-9]{32}/[a-f0-9]{32})', re.I)
	USER_FIELD_REGEX = re.compile(r'user.+', re.I)
	REDIRECT_FIELD_REGEX = re.compile(r'redirect.+', re.I)
	NAMES_REGEX = re.compile(r'name[\'\"= ]{1,4}notesview[\'\"]?', re.I)
	WEBADMIN_REGEX = re.compile(r'<title>.*administration</title>', re.I)
	RESTRICTED_REGEX = re.compile(r'(notes exception|not authorized)', re.I)
	VERSION_REGEX = re.compile(r'(?:version|domino administrator|domino|release)[=":\s]{0,4}([\d.]+)(?:\s|\")?', re.I)
	LINUX_USER_REGEX = re.compile(r'([a-z0-9-_].+):(.+)', re.I)
	WINDOWS_USER_REGEX = re.compile(r'(.+)\\(.+)', re.I)
	PATH_REGEX = re.compile(r'DataDirectory\s*=\s*\'(.+)\';', re.I)

	def set_logging(self):
		"""
		Configure the basic logging environment for the application.
		"""
		logger = logging.getLogger('DomiOwned')
		logger.setLevel(logging.DEBUG)
		custom_format = CustomLoggingFormatter()
		handler = logging.StreamHandler()
		handler.setFormatter(custom_format)
		logger.addHandler(handler)

		return logger

	def parse_credentials(self, value):
		"""
		Handle credentials if value is None.
		"""
		return '' if value is None else value

	def check_url(self, url):
		"""
		Check for valid base URL.
		"""
		if self.URL_REGEX.search(url):
			return self.URL_REGEX.search(url).group(1)
		else:
			self.logger.error('Invalid URL provided')
			sys.exit()

	def setup_progress(self, total):
		"""
		Setup progress bar.
		"""
		progress_bar = tqdm.tqdm(
			total=total,
			desc="Progress",
			smoothing=0.5,
			bar_format='{desc}{percentage:3.0f}%|{bar}|({n_fmt}/{total_fmt})|{elapsed} '
		)

		return progress_bar


class CustomLoggingFormatter(logging.Formatter):
	"""
	Custom logging formatter.
	"""
	DEBUG_FORMAT = "\033[1m\033[34m[*]\033[0m %(msg)s"
	INFO_FORMAT = "\033[1m\033[32m[+]\033[0m %(msg)s"
	WARN_FORMAT = "\033[1m\033[33m[!]\033[0m %(msg)s"
	ERROR_FORMAT = "\033[1m\033[31m[-]\033[0m %(msg)s"

	def __init__(self):
		super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')

	def format(self, record):
		orig_format = self._style._fmt

		if record.levelno == logging.DEBUG:
			self._style._fmt = CustomLoggingFormatter.DEBUG_FORMAT
		elif record.levelno == logging.INFO:
			self._style._fmt = CustomLoggingFormatter.INFO_FORMAT
		elif record.levelno == logging.WARN:
			self._style._fmt = CustomLoggingFormatter.WARN_FORMAT
		elif record.levelno == logging.ERROR:
			self._style._fmt = CustomLoggingFormatter.ERROR_FORMAT

		result = logging.Formatter.format(self, record)
		self._style._fmt = orig_format

		return result


class Banner(object):
	"""
	Domi-Owned visual banner.
	"""
	SHOW = """
         __________   __________ __________ 
        |          |\|          |          |\\
        |  *    *  |||  *  *  * |        * ||
        |  *    *  |||          |     *    ||
        |  *    *  |||  *  *  * |  *       ||
        |__________|||__________|__________||
        |          || `---------------------`
        |  *    *  ||
        |          ||
        |  *    *  ||
        |__________||
         `----------`

             IBM/Lotus Domino OWNage
"""
