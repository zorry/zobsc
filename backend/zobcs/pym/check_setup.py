from __future__ import print_function
import portage
import os
import errno

from portage.exception import DigestException, FileNotFound, ParseError, PermissionDenied
from zobcs.text import get_file_text
from zobcs.readconf import get_conf_settings
from zobcs.mysql_querys import get_config_id, get_config_list_all, add_zobcs_logs, get_config, \
	update_make_conf, get_profile_checksum

reader=get_conf_settings()
zobcs_settings_dict=reader.read_zobcs_settings_all()
_config = zobcs_settings_dict['zobcs_config']
_hostname =zobcs_settings_dict['hostname']

def check_make_conf(conn):
	_config_id = get_config_id(conn, _config, _hostname)
	# Get the config list
	config_id_list_all = get_config_list_all(conn)
	log_msg = "Checking configs for changes and errors"
	add_zobcs_logs(conn, log_msg, "info", _config_id)
	configsDict = {}
	for config_id in config_id_list_all:
		attDict={}
		# Set the config dir
		hostname, config = get_config(conn, config_id)
		check_config_dir = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + hostname +"/" + config + "/"
		make_conf_file = check_config_dir + "etc/portage/make.conf"
		# Check if we can take a checksum on it.
		# Check if we have some error in the file. (portage.util.getconfig)
		# Check if we envorment error with the config. (settings.validate)
		try:
			make_conf_checksum_tree = portage.checksum.sha256hash(make_conf_file)[0]
			portage.util.getconfig(make_conf_file, tolerant=0, allow_sourcing=True, expand=True)
			mysettings = portage.config(config_root = check_config_dir)
			mysettings.validate()
			# With errors we update the db on the config and disable the config
		except ParseError as e:
			attDict['config_error'] =  str(e)
			attDict['active'] = 'False'
			log_msg = "%s FAIL!" % (config,)
			add_zobcs_logs(conn, log_msg, "info", _config_id)
		else:
			attDict['config_error'] = ''
			attDict['active'] = 'True'
			log_msg = "%s PASS" % (config,)
			add_zobcs_logs(conn, log_msg, "info", _config_id)
		attDict['make_conf_text'] = get_file_text(make_conf_file)
		attDict['make_conf_checksum_tree'] = make_conf_checksum_tree
		configsDict[config_id]=attDict
	update_make_conf(conn, configsDict)
	log_msg = "Checking configs for changes and errors ... Done"
	add_zobcs_logs(conn, log_msg, "info", _config_id)

def check_make_conf_guest(session, config_id):
	make_conf_file = "/etc/portage/make.conf"
	# Check if we can open the file and close it
	# Check if we have some error in the file (portage.util.getconfig)
	# Check if we envorment error with the config (settings.validate)
	try:
		make_conf_checksum_tree = portage.checksum.sha256hash(make_conf_file)[0]
		portage.util.getconfig(make_conf_file, tolerant=0, allow_sourcing=True, expand=True)
		mysettings = portage.config(config_root = "/")
		mysettings.validate()
		# With errors we return false
	except Exception as e:
		return False
	make_conf_checksum_db = get_profile_checksum(session, config_id)
	if make_conf_checksum_db is None:
		return False
	print('make_conf_checksum_tree', make_conf_checksum_tree)
	print('make_conf_checksum_db', make_conf_checksum_db)
	if make_conf_checksum_tree != make_conf_checksum_db:
		return False
	return True

def check_configure_guest(session, config_id):
	pass_make_conf = check_make_conf_guest(conn, config_id)
	print(pass_make_conf)
	return pass_make_conf