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

def process_url(url):
	url_regex = re.compile('https?://[a-z0-9\-.:]+', re.I)
	if url_regex.search(url):
		target = url_regex.search(url).group(0)
	else:
		target = None

	return target

def print_error(msg):
	print "\033[1m\033[31m[-]\033[0m {0}".format(msg)
	
def print_status(msg):
	print "\033[1m\033[34m[*]\033[0m {0}".format(msg)
		
def print_good(msg):
	print "\033[1m\033[32m[+]\033[0m {0}".format(msg)
	
def print_warn(msg):
	print "\033[1m\033[33m[!]\033[0m {0}".format(msg)