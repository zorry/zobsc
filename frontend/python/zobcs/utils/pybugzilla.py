from __future__ import print_function
import commands
import getpass
from http.cookiejar import CookieJar, LWPCookieJar
import locale
import mimetypes
import os
import subprocess
import re
import sys
import tempfile
import textwrap
import xmlrpc.client

try:
	import readline
except ImportError:
	readline = None

from bugz.bugzilla import BugzillaProxy
from bugz.errhandling import BugzError
from bugz.log import log_info
from django.conf import settings

BUGZ_COMMENT_TEMPLATE = \
"""
BUGZ: ---------------------------------------------------
%s
BUGZ: Any line beginning with 'BUGZ:' will be ignored.
BUGZ: ---------------------------------------------------
"""

DEFAULT_COOKIE_FILE = '.bugz_cookie'

#
# Auxiliary functions
#

def get_content_type(filename):
	return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

#
# Bugz specific exceptions
#

class BugzError(Exception):
	pass

class PrettyBugz:
	def __init__(self):
		self.quiet = True
		self.columns = 80
		self.user = settings.BUGZILLA_USER
		self.password = settings.BUGZILLA_PASS
		self.url = settings.BUGZILLA_URL

		# FIXME: the cookie file need to have random ending. and stored in /tmp
		cookie_file = os.path.join('/tmp/', DEFAULT_COOKIE_FILE)
		self.cookiejar = LWPCookieJar(cookie_file)

		try:
			self.cookiejar.load()
		except IOError:
			pass

		self.enc = 'utf-8'

		self.log("Using %s " % self.url)
		self.bz = BugzillaProxy(self.url, cookiejar=self.cookiejar)

	def log(self, status_msg, newline = True):
		if not self.quiet:
			if newline:
				print( ' * %s' % status_msg)
			else:
				print( ' * %s\n' % status_msg)

	def warn(self, warn_msg):
		if not self.quiet:
			print( ' ! Warning: %s' % warn_msg)


	def bzcall(self, method, *args):
		"""Attempt to call method with args. Log in if authentication is required.
		"""
		try:
			self.login()
			return method(*args)
		except xmlrpclib.Fault as fault:
			# Fault code 410 means login required
			if fault.faultCode == 410:
				self.login()
				return method(*args)
			raise

	def login(self, args=None):
		"""Authenticate a session.
		"""

		# perform login
		params = {}
		params['login'] = self.user
		params['password'] = self.password
		if args is not None:
			params['remember'] = True
		self.log('Logging in')
		self.bz.User.login(params)

		if args is not None:
			self.cookiejar.save()
			os.chmod(self.cookiejar.filename, 0600)

	def logout(self, args):
		self.log('logging out')
		self.bz.User.logout()

	def post(self, args):
		"""Post a new bug"""

		params={}
		params['product'] = args['product']
		params['component'] = args['component']
		params['version'] = args['version']
		params['summary'] = args['summary']
		if args['description'] is not None:
			params['description'] = args['description']
		if args['assigned_to'] is not None:
			params['assigned_to'] = args['assigned_to']
		
		result = self.bzcall(self.bz.Bug.create, params)
		self.log('Bug %d submitted' % result['id'])
		return result

	def modify(self, args):
		"""Modify an existing bug (eg. adding a comment or changing resolution.)"""

		params = {}
		if args['cc_add'] is not None:
			params['cc'] = {}
		if args['comment'] is not None:
			params['comment'] = {}
		params['ids'] = args['bugid']
		if args['assigned_to'] is not None:
			params['assigned_to'] = args['assigned_to']
		if args['cc_add'] is not None:
			params['cc']['add'] = args['cc_add']
		if args['comment'] is not None:
			params['comment']['body'] = args['comment']

		if len(params) < 2:
			raise BugzError('No changes were specified')
		result = self.bzcall(self.bz.Bug.update, params)
		for bug in result['bugs']:
			changes = bug['changes']
			if not len(changes):
				self.log('Added comment to bug %s' % bug['id'])
			else:
				self.log('Modified the following fields in bug %s' % bug['id'])
				for key in changes.keys():
					self.log('%-12s: removed %s' %(key, changes[key]['removed']))
					self.log('%-12s: added %s' %(key, changes[key]['added']))

	def attach(self, args):
		""" Attach a file to a bug given a filename. """
		filename = args['filename']

		if not os.path.exists(filename):
			raise BugzError('File not found: %s' % filename)

		params = {}
		params['ids'] = args['bugid']

		fd = open(filename, 'rb')
		params['data'] = xmlrpclib.Binary(fd.read())
		fd.close()

		params['file_name'] = os.path.basename(filename)
		params['summary'] = params['file_name']
		params['content_type'] = args['content_type']
		params['comment'] = args['comment_attach']
		result =  self.bzcall(self.bz.Bug.add_attachment, params)
		self.log("'%s' has been attached to bug %s" % (filename, args['bugid']))
