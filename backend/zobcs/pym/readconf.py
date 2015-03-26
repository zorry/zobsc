import os
import sys
import re
from socket import getfqdn

class get_conf_settings(object):
# open the /etc/zobcs/zobcs.conf file and get the needed
# settings for zobcs
	def __init__(self):
		self.configfile = "/etc/zobcs/zobcs.conf"

	def read_zobcs_settings_all(self):
	# It will return a dict with options from the configfile
		try:
			open_conffile = open(self.configfile, 'r')
		except:
			sys.exit("Fail to open config file:" + self.configfile)
		textlines = open_conffile.readlines()
		for line in textlines:
			element = line.split('=')
			if element[0] == 'SQLBACKEND':		# Databas backend
				get_sql_backend = element[1]
			if element[0] == 'SQLDB':			# Database
				get_sql_db = element[1]
			if element[0] == 'SQLHOST':			# Host
				get_sql_host = element[1]
			if element[0] == 'SQLUSER':			# User
				get_sql_user = element[1]
			if element[0] == 'SQLPASSWD':		# Password
				get_sql_passwd = element[1]
			# Buildhost root (dir for host/setup on host)
			if element[0] == 'ZOBCSGITREPONAME':
				get_zobcs_gitreponame = element[1]
			# Buildhost setup (host/setup on guest)
			if element[0] == 'ZOBCSCONFIG':
				get_zobcs_config = element[1]
			# if element[0] == 'LOGFILE':
			#	get_zobcs_logfile = element[1]
		open_conffile.close()

		zobcs_settings_dict = {}
		zobcs_settings_dict['sql_backend'] = get_sql_backend.rstrip('\n')
		zobcs_settings_dict['sql_db'] = get_sql_db.rstrip('\n')
		zobcs_settings_dict['sql_host'] = get_sql_host.rstrip('\n')
		zobcs_settings_dict['sql_user'] = get_sql_user.rstrip('\n')
		zobcs_settings_dict['sql_passwd'] = get_sql_passwd.rstrip('\n')
		zobcs_settings_dict['zobcs_gitreponame'] = get_zobcs_gitreponame.rstrip('\n')
		zobcs_settings_dict['zobcs_config'] = get_zobcs_config.rstrip('\n')
		zobcs_settings_dict['hostname'] = getfqdn()
		# zobcs_settings_dict['zobcs_logfile'] = get_zobcs_logfile.rstrip('\n')
		return zobcs_settings_dict

def read_config_settings():
	reader = get_conf_settings()
	return reader.read_zobcs_settings_all()
