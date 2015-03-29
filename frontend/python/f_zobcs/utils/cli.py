# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import getpass
from http.cookiejar import CookieJar, LWPCookieJar
import locale
import mimetypes
import os
import re
import subprocess
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

BUGZ_COMMENT_TEMPLATE = \
"""
BUGZ: ---------------------------------------------------
%s
BUGZ: Any line beginning with 'BUGZ:' will be ignored.
BUGZ: ---------------------------------------------------
"""

DEFAULT_COOKIE_FILE = '.bugz_cookie'
DEFAULT_TOKEN_FILE = '.bugz_token'
DEFAULT_NUM_COLS = 80

#
# Auxiliary functions
#

def get_content_type(filename):
	return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

class PrettyBugz:
	def __init__(self, args):
		self.user = args['user']
		self.password = args['password']
		self.skip_auth = args['skip_auth']

		cookie_file = os.path.join(os.environ['HOME'], DEFAULT_COOKIE_FILE)
		self.cookiejar = LWPCookieJar(cookie_file)

		try:
			self.cookiejar.load()
		except IOError:
			pass

		self.token_file = os.path.join(os.environ['HOME'], DEFAULT_TOKEN_FILE)
		try:
			self.token = open(self.token_file).read().strip()
		except IOError:
			self.token = None

		log_info("Using %s " % args['url'])
		self.bz = BugzillaProxy(args['url'], cookiejar=self.cookiejar)

	def set_token(self, *args):
		if args and self.token:
			args[0]['Bugzilla_token'] = self.token
		return args

	def call_bz(self, method, *args):
		"""Attempt to call method with args. Log in if authentication is required.
		"""
		try:
			return method(*self.set_token(*args))
		except xmlrpc.client.Fault as fault:
			# Fault code 410 means login required
			if fault.faultCode == 410 and not self.skip_auth:
				self.login()
				return method(*self.set_token(*args))
			raise

	def login(self, args=None):
		# Authenticate a session.
		# perform login
		params = {}
		params['login'] = self.user
		params['password'] = self.password
		if args is not None:
			params['remember'] = True
		log_info('Logging in')
		try:
			self.bz.User.login(params)
		except xmlrpc.client.Fault as fault:
			raise BugzError("Can't login: " + fault.faultString)
		log_info('Logging in')
		result = self.bz.User.login(params)
		if 'token' in result:
			self.token = result['token']

		if args is not None:
			if self.token:
				fd = open(self.token_file, 'w')
				fd.write(self.token)
				fd.write('\n')
				fd.close()
				os.chmod(self.token_file, 0o600)
			else:
				self.cookiejar.save()
				os.chmod(self.cookiejar.filename, 0o600)

	def logout(self, args):
		log_info('logging out')
		try:
			self.bz.User.logout()
		except xmlrpc.client.Fault as fault:
			raise BugzError("Failed to logout: " + fault.faultString)

	def search(self, args):
		"""Performs a search on the bugzilla database with the keywords given on the title (or the body if specified).
		"""
		valid_keys = ['alias', 'assigned_to', 'component', 'creator',
			'limit', 'offset', 'op_sys', 'platform',
			'priority', 'product', 'resolution',
			'severity', 'status', 'version', 'whiteboard']

		search_opts = sorted([(opt, val) for opt, val in list(args.__dict__.items())
			if val is not None and opt in valid_keys])

		params = {}
		for key in args.__dict__:
			if key in valid_keys and getattr(args, key) is not None:
				params[key] = getattr(args, key)
		if getattr(args, 'terms'):
			params['summary'] = args.terms

		search_term = ' '.join(args.terms).strip()

		if not (params or search_term):
			raise BugzError('Please give search terms or options.')

		if search_term:
			log_msg = 'Searching for \'%s\' ' % search_term
		else:
			log_msg = 'Searching for bugs '

		if search_opts:
			log_info(log_msg + 'with the following options:')
			for opt, val in search_opts:
				log_info('   %-20s = %s' % (opt, val))
		else:
			log_info(log_msg)

		if 'status' not in params:
			params['status'] = ['CONFIRMED', 'IN_PROGRESS', 'UNCONFIRMED']
		else:
			for x in params['status'][:]:
				if x in ['all', 'ALL']:
					del params['status']

		result = self.call_bz(self.bz.Bug.search, params)['bugs']

		if not len(result):
			log_info('No bugs found.')
		else:
			self.list_bugs(result, args)

	def get(self, args):
		""" Fetch bug details given the bug id """
		log_info('Getting bug %s ..' % args['bugid'])
		try:
			result = self.call_bz(self.bz.Bug.get, {'ids':[args['bugid']]})
		except xmlrpc.client.Fault as fault:
			raise BugzError("Can't get bug #" + str(args['bugid']) + ": " \
					+ fault.faultString)

		for bug in result['bugs']:
			self.show_bug_info(bug, args.attachments, args.comments)

	def post(self, args):
		"""Post a new bug"""

		params={}
		params['product'] = args['product']
		params['component'] = args['component']
		params['summary'] = args['summary']
		params['description'] = args['description']
		#params['assigned_to'] = args['assigned_to']
		params['version'] = args['version']
		
		result = self.call_bz(self.bz.Bug.create, params)
		log_info('Bug %d submitted' % result['id'])
		return result

	def modify(self, args):
		"""Modify an existing bug (eg. adding a comment or changing resolution.)"""

		params = {}
		if args['cc_add'] is not None:
			params['cc'] = {}
		if args['comment'] is not None:
			params['comment'] = {}
		params['ids'] = args['bugid']
		# if args['assigned_to'] is not None:
		# params['assigned_to'] = args['assigned_to']
		if args['cc_add'] is not None:
			params['cc']['add'] = args['cc_add']
		if args['comment'] is not None:
			params['comment']['body'] = args['comment']

		if len(params) < 2:
			raise BugzError('No changes were specified')
		result = self.call_bz(self.bz.Bug.update, params)
		for bug in result['bugs']:
			changes = bug['changes']
			if not len(changes):
				log_info('Added comment to bug %s' % bug['id'])
			else:
				log_info('Modified the following fields in bug %s' % bug['id'])
				for key in changes:
					log_info('%-12s: removed %s' %(key, changes[key]['removed']))
					log_info('%-12s: added %s' %(key, changes[key]['added']))

	def attachment(self, args):
		""" Download or view an attachment given the id."""
		log_info('Getting attachment %s' % args.attachid)

		params = {}
		params['attachment_ids'] = [args.attachid]
		result = self.call_bz(self.bz.Bug.attachments, params)
		result = result['attachments'][args.attachid]

		action = {True:'Viewing', False:'Saving'}
		log_info('%s attachment: "%s"' %
			(action[args.view], result['file_name']))
		safe_filename = os.path.basename(re.sub(r'\.\.', '',
												result['file_name']))

		if args.view:
			print(result['data'].data)
		else:
			if os.path.exists(result['file_name']):
				raise RuntimeError('Filename already exists')

			fd = open(safe_filename, 'wb')
			fd.write(result['data'].data)
			fd.close()

	def attach(self, args):
		""" Attach a file to a bug given a filename. """
		filename = args['filename']
		summary = os.path.basename(filename)
		comment = args['comment']

		if not os.path.exists(filename):
			raise BugzError('File not found: %s' % filename)

		params = {}
		params['ids'] = args['bugid']

		fd = open(filename, 'rb')
		params['data'] = xmlrpc.client.Binary(fd.read())
		fd.close()

		params['file_name'] = os.path.basename(filename)
		params['summary'] = summary
		params['content_type'] = args['content_type']
		params['comment'] = comment
		#params['is_patch'] = is_patch
		result =  self.call_bz(self.bz.Bug.add_attachment, params)
		log_info("'%s' has been attached to bug %s" % (filename, args['bugid']))

	def list_bugs(self, buglist, args):
		for bug in buglist:
			bugid = bug['id']
			status = bug['status']
			priority = bug['priority']
			severity = bug['severity']
			assignee = bug['assigned_to'].split('@')[0]
			desc = bug['summary']
			line = '%s' % (bugid)
			if args.show_status:
				line = '%s %-12s' % (line, status)
			if args.show_priority:
				line = '%s %-12s' % (line, priority)
			if args.show_severity:
				line = '%s %-12s' % (line, severity)
			line = '%s %-20s' % (line, assignee)
			line = '%s %s' % (line, desc)
			print(line[:self.columns])

		log_info("%i bug(s) found." % len(buglist))

	def show_bug_info(self, bug, show_attachments, show_comments):
		FieldMap = {
			'alias': 'Alias',
			'summary': 'Title',
			'status': 'Status',
			'resolution': 'Resolution',
			'product': 'Product',
			'component': 'Component',
			'version': 'Version',
			'platform': 'Hardware',
			'op_sys': 'OpSystem',
			'priority': 'Priority',
			'severity': 'Severity',
			'target_milestone': 'TargetMilestone',
			'assigned_to': 'AssignedTo',
			'url': 'URL',
			'whiteboard': 'Whiteboard',
			'keywords': 'Keywords',
			'depends_on': 'dependsOn',
			'blocks': 'Blocks',
			'creation_time': 'Reported',
			'creator': 'Reporter',
			'last_change_time': 'Updated',
			'cc': 'CC',
			'see_also': 'See Also',
		}
		SkipFields = ['is_open', 'id', 'is_confirmed',
				'is_creator_accessible', 'is_cc_accessible',
				'update_token']

		for field in bug:
			if field in SkipFields:
				continue
			if field in FieldMap:
				desc = FieldMap[field]
			else:
				desc = field
			value = bug[field]
			if field in ['cc', 'see_also']:
				for x in value:
					print('%-12s: %s' %  (desc, x))
			elif isinstance(value, list):
				s = ', '.join(["%s" % x for x in value])
				if s:
					print('%-12s: %s' % (desc, s))
			elif value is not None and value != '':
				print('%-12s: %s' % (desc, value))

		if show_attachments:
			bug_attachments = self.call_bz(self.bz.Bug.attachments, {'ids':[bug['id']]})
			bug_attachments = bug_attachments['bugs']['%s' % bug['id']]
			print('%-12s: %d' % ('Attachments', len(bug_attachments)))
			print()
			for attachment in bug_attachments:
				aid = attachment['id']
				desc = attachment['summary']
				when = attachment['creation_time']
				print('[Attachment] [%s] [%s]' % (aid, desc))

		if show_comments:
			bug_comments = self.call_bz(self.bz.Bug.comments, {'ids':[bug['id']]})
			bug_comments = bug_comments['bugs']['%s' % bug['id']]['comments']
			print()
			print('%-12s: %d' % ('Comments', len(bug_comments)))
			print()
			i = 0
			wrapper = textwrap.TextWrapper(width = self.columns,
				break_long_words = False,
				break_on_hyphens = False)
			for comment in bug_comments:
				who = comment['creator']
				when = comment['time']
				what = comment['text']
				print('[Comment #%d] %s : %s' % (i, who, when))
				print('-' * (self.columns - 1))

				if what is None:
					what = ''

				# print wrapped version
				for line in what.split('\n'):
					if len(line) < self.columns:
						print(line)
					else:
						for shortline in wrapper.wrap(line):
							print(shortline)
				print()
				i += 1
