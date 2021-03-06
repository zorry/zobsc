# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import logging

def NewConnection(zobcs_settings_dict):
	backend=zobcs_settings_dict['sql_backend']
	host=zobcs_settings_dict['sql_host']
	user=zobcs_settings_dict['sql_user']
	password=zobcs_settings_dict['sql_passwd']
	database=zobcs_settings_dict['sql_db']
	if backend == 'mysql':
		try:
			from sqlalchemy import create_engine
		except ImportError:
			print("Please install a recent version of dev-python/sqlalchemy for Python")
			sys.exit(1)
		logging.basicConfig()
		logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
		mysqldriver = 'mysql+mysqlconnector'
		return create_engine(mysqldriver + '://' + user + ':' + password + '@' + host + '/' + database, pool_recycle=120)
