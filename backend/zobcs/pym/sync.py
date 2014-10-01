from __future__ import print_function
import portage
import os
import errno
import sys
# Do not support python 3.*
from git import *

from _emerge.main import emerge_main
from zobcs.readconf import get_conf_settings
from zobcs.mysql_querys import get_config_id, add_zobcs_logs, get_default_config

reader=get_conf_settings()
zobcs_settings_dict=reader.read_zobcs_settings_all()
_config = zobcs_settings_dict['zobcs_config']
_hostname =zobcs_settings_dict['hostname']

def git_pull(conn):
	#FIXME: Use git direct so we can use python 3.*
	config_id = get_config_id(conn, _config, _hostname)
	log_msg = "Git pull"
	add_zobcs_logs(conn, log_msg, "info", config_id)
	repo = Repo("/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/")
	repo_remote = repo.remotes.origin
	repo_remote.pull()
	master = repo.head.reference
	log_msg = "Git log: %s" % (master.log(),)
	add_zobcs_logs(conn, log_msg, "info", config_id)
	log_msg = "Git pull ... Done"
	add_zobcs_logs(conn, log_msg, "info", config_id)
	return True

def sync_tree(conn):
	config_id = get_config_id(conn, _config, _hostname)
	host_config = _hostname +"/" + _config
	default_config_root = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + host_config + "/"
	mysettings = portage.config(config_root = default_config_root)
	tmpcmdline = []
	tmpcmdline.append("--sync")
	tmpcmdline.append("--quiet")
	tmpcmdline.append("--config-root=" + default_config_root)
	log_msg = "Emerge --sync"
	add_zobcs_logs(conn, log_msg, "info", config_id)
	fail_sync = emerge_main(args=tmpcmdline)
	if not conn.is_connected() is True:
		conn.reconnect(attempts=2, delay=1)
	if fail_sync is True:
		log_msg = "Emerge --sync fail!"
		add_zobcs_logs(conn, log_msg, "error", config_id)
		return False
	else:
		# Need to add a config dir so we can use profiles/base for reading the tree.
		# We may allready have the dir on local repo when we sync.
		try:
			os.mkdir(mysettings['PORTDIR'] + "/profiles/config", 0o777)
			with open(mysettings['PORTDIR'] + "/profiles/config/parent", "w") as f:
				f.write("../base\n")
				f.close()
		except:
			pass
		log_msg = "Emerge --sync ... Done."
		add_zobcs_logs(conn, log_msg, "info", config_id)
	return True
