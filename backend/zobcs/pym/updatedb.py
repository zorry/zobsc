# Distributed under the terms of the GNU General Public License v2

""" 	This code will update the sql backend with needed info for
	the Frontend and the Guest deamons. """
from __future__ import print_function
import sys
import os
import multiprocessing
import portage

from zobcs.ConnectionManager import connectionManager
from zobcs.mysql_querys import get_config_id, add_zobcs_logs, get_default_config, get_package_id, update_repo_db, \
	update_categories_db
from zobcs.check_setup import check_make_conf
from zobcs.package import zobcs_package
# Get the options from the config file set in zobcs.readconf
from zobcs.readconf import get_conf_settings
reader = get_conf_settings()
zobcs_settings_dict=reader.read_zobcs_settings_all()
_config = zobcs_settings_dict['zobcs_config']
_hostname =zobcs_settings_dict['hostname']

def init_portage_settings(conn, config_id):
	# check config setup
	check_make_conf(conn)
	log_msg = "Check configs done"
	add_zobcs_logs(conn, log_msg, "info", config_id)
	
	# Get default config from the configs table  and default_config=1
	host_config = _hostname +"/" + _config
	default_config_root = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + host_config + "/"

	# Set config_root (PORTAGE_CONFIGROOT)  to default_config_root
	mysettings = portage.config(config_root = default_config_root)
	log_msg = "Setting default config to: %s" % (host_config,)
	add_zobcs_logs(conn, log_msg, "info", config_id)
	return mysettings

def update_cpv_db_pool(mysettings, myportdb, cp, repo):
	CM = connectionManager()
	conn = CM.newConnection()
	init_package = zobcs_package(conn, mysettings, myportdb)

	# split the cp to categories and package
	element = cp.split('/')
	categories = element[0]
	package = element[1]

	# update the categories table
	update_categories_db(conn, categories)

	# Check if we have the cp in the package table
	package_id = get_package_id(conn, categories, package, repo)
	if package_id is None:  
		# Add new package with ebuilds
		init_package.add_new_package_db(cp, repo)
	else:
		# Update the packages with ebuilds
		init_package.update_package_db(package_id)
	conn.close()

def update_cpv_db(conn, config_id):
	mysettings =  init_portage_settings(conn, config_id)
	log_msg = "Checking categories, package, ebuilds"
	add_zobcs_logs(conn, log_msg, "info", config_id)
	
	# Setup portdb, package
	myportdb = portage.portdbapi(mysettings=mysettings)
	repo_list = ()
	repos_trees_list = []

	# Use all cores when multiprocessing
	pool_cores= multiprocessing.cpu_count()
	pool = multiprocessing.Pool(processes=pool_cores)

	# Will run some update checks and update package if needed

	# Get the repos and update the repos db
	repo_list = myportdb.getRepositories()
	update_repo_db(conn, repo_list)

	# Close the db for the multiprocessing pool will make new ones
	# and we don't need this one for some time.
	conn.close()

	# Get the rootdirs for the repos
	repo_trees_list = myportdb.porttrees
	for repo_dir in repo_trees_list:
		repo = myportdb.getRepositoryName(repo_dir)
		repo_dir_list = []
		repo_dir_list.append(repo_dir)

		# Get the package list from the repo
		package_list_tree = myportdb.cp_all(trees=repo_dir_list)

		# Run the update package for all package in the list and in a multiprocessing pool
		for cp in sorted(package_list_tree):
			pool.apply_async(update_cpv_db_pool, (mysettings, myportdb, cp, repo,))
			# update_cpv_db_pool(mysettings, myportdb, cp, repo)

	# close and join the multiprocessing pools
	pool.close()
	pool.join()

	# reconnect to the db if needed.
	if not conn.is_connected() is True:
		conn.reconnect(attempts=2, delay=1)
	log_msg = "Checking categories, package and ebuilds ... done"
	add_zobcs_logs(conn, log_msg, "info", config_id)

def update_db_main(conn):
	# Main

	# Logging
	config_id = get_config_id(conn, _config, _hostname)
	log_msg = "Update db started."
	add_zobcs_logs(conn, log_msg, "info", config_id)

	# Update the cpv db
	update_cpv_db(conn, config_id)
	log_msg = "Update db ... Done."
	add_zobcs_logs(conn, log_msg, "info", config_id)
	return True
