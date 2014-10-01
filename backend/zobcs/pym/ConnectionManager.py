from __future__ import print_function
from zobcs.readconf import get_conf_settings
reader = get_conf_settings()
zobcs_settings_dict=reader.read_zobcs_settings_all()

class connectionManager(object):

	def __init__(self):
		self._backend=zobcs_settings_dict['sql_backend']
		self._host=zobcs_settings_dict['sql_host']
		self._user=zobcs_settings_dict['sql_user']
		self._password=zobcs_settings_dict['sql_passwd']
		self._database=zobcs_settings_dict['sql_db']

	def newConnection(self):
		if self._backend == 'mysql':
			try:
				import mysql.connector
				from mysql.connector import errorcode
			except ImportError:
				print("Please install a recent version of dev-python/mysql-connector-python for Python")
				sys.exit(1)
			db_config = {}
			db_config['user'] = self._user
			db_config['password'] = self._password
			db_config['host'] = self._host
			db_config['database'] = self._database
			db_config['raise_on_warnings'] = True
			try:
				cnx = mysql.connector.connect(**db_config)
			except mysql.connector.Error as err:
				if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
					print("Something is wrong your username or password")
				elif err.errno == errorcode.ER_BAD_DB_ERROR:
					print("Database does not exists")
				else:
					print(err)
		return cnx
