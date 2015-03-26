# Distributed under the terms of the GNU General Public License v2

""" 	This code will update the sql backend with needed info for
	the Frontend and the Guest deamons. """
from __future__ import print_function
import sys
import os
import multiprocessing
import time
import portage
from sqlalchemy.orm import scoped_session, sessionmaker
from zobcs.ConnectionManager import NewConnection
from zobcs.sqlquerys import add_zobcs_logs, get_package_info, update_repo_db, \
	update_categories_db, get_configmetadata_info, get_config_all_info, add_new_build_job, \
	get_config_info
from zobcs.check_setup import check_make_conf
from zobcs.package import zobcs_package
# Get the options from the config file set in zobcs.readconf
from zobcs.readconf import get_conf_settings

def init_portage_settings(session, config_id, zobcs_settings_dict):
	# check config setup
	check_make_conf(session, config_id, zobcs_settings_dict)
	log_msg = "Check configs done"
	add_zobcs_logs(session, log_msg, "info", config_id)
	
	# Get default config from the configs table  and default_config=1
	host_config = zobcs_settings_dict['hostname'] +"/" + zobcs_settings_dict['zobcs_config']
	default_config_root = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + host_config + "/"

	# Set config_root (PORTAGE_CONFIGROOT)  to default_config_root
	mysettings = portage.config(config_root = default_config_root)
	log_msg = "Setting default config to: %s" % (host_config,)
	add_zobcs_logs(session, log_msg, "info", config_id)
	return mysettings

def update_cpv_db_pool(mysettings, myportdb, cp, repo, zobcs_settings_dict, config_id):
	session_factory = sessionmaker(bind=NewConnection(zobcs_settings_dict))
	Session = scoped_session(session_factory)
	session2 = Session()
	init_package = zobcs_package(session2, mysettings, myportdb, config_id, zobcs_settings_dict)

	# split the cp to categories and package
	element = cp.split('/')
	categories = element[0]
	package = element[1]

	# update the categories table
	update_categories_db(session2, categories)

	# Check if we have the cp in the package table
	PackagesInfo = get_package_info(session2, categories, package, repo)
	if PackagesInfo:  
		# Update the packages with ebuilds
		new_build_jobs = init_package.update_package_db(PackagesInfo.PackageId)
	else:
		# Add new package with ebuilds
		new_build_jobs =init_package.add_new_package_db(cp, repo)
	Session.remove()
	return new_build_jobs

def add_builds_jobs (session, new_build_jobs_list, config_id):
	SyncConfigs = {}
	for ConfigInfoAll in get_config_all_info(session):
		ConfigMetadata = get_configmetadata_info(session, ConfigInfoAll.ConfigId)
		if ConfigMetadata.ConfigSync:
			try:
				SyncConfigs[ConfigInfoAll.Config]['Syncedconfigs'] = SyncConfigs[ConfigInfoAll.Config]['Syncedconfigs'] + 1
				SyncConfigs[ConfigInfoAll.Config]['Syncedconfigslist'].append(ConfigInfoAll.ConfigId)
			except KeyError as e:
				attd = {}
				attd['Syncedconfigs'] = 1
				attd['Next'] = 0
				attd['id'] = ConfigInfoAll.ConfigId
				attd['ebuild_id'] = 0
				attd['Syncedconfigslist'] = []
				attd['Syncedconfigslist'].append(ConfigInfoAll.ConfigId)
				SyncConfigs[ConfigInfoAll.Config] = attd

	for new_build_jobs_dict in new_build_jobs_list:
		for k, v in new_build_jobs_dict.items():
			ConfigMetadata = get_configmetadata_info(session, k)
			ConfigInfo = get_config_info(session, k)
			if not ConfigMetadata.ConfigSync:
				add_new_build_job(session, v['ebuild_id'], k, v['use_flagsDict'])
				# B = Build cpv use-flags config
				# FIXME log_msg need a fix to log the use flags corect.
				log_msg = "B %s:%s USE: %s %s:%s" % (k, v['repo'], v['use_flagsDict'], ConfigInfo.Hostname, ConfigInfo.Config,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				for b, l in SyncConfigs.items():
					if k in l['Syncedconfigslist'] and l['ebuild_id'] != v['ebuild_id'] and l['id'] == k:
						add_new_build_job(session, v['ebuild_id'], k, v['use_flagsDict'])
						SyncConfigs[b]['ebuild_id'] = v['ebuild_id']
						SyncConfigs[b]['id'] = SyncConfigs[b]['Syncedconfigslist'][SyncConfigs[b]['Next']]
						if SyncConfigs[b]['Next'] == SyncConfigs[b]['Syncedconfigs'] - 1:
							SyncConfigs[b]['Next'] = 0
						else:
							SyncConfigs[b]['Next'] = SyncConfigs[b]['Next'] + 1
						# B = Build cpv use-flags config
						# FIXME log_msg need a fix to log the use flags corect.
						log_msg = "B %s:%s USE: %s %s:%s" % (k, v['repo'], v['use_flagsDict'], ConfigInfo.Hostname, ConfigInfo.Config,)
						add_zobcs_logs(session, log_msg, "info", config_id)

def update_cpv_db(session, config_id, zobcs_settings_dict):
	GuestBusy = True
	log_msg = "Waiting for Guest to be idel"
	add_zobcs_logs(session, log_msg, "info", config_id)
	guestid_list = []
	for config in get_config_all_info(session):
		if not config.Host:
			guestid_list.append(config.ConfigId)
	while GuestBusy:
		Status_list = []
		for guest_id in guestid_list:
			ConfigMetadata = get_configmetadata_info(session, guest_id)
			Status_list.append(ConfigMetadata.Status)
		if not 'Runing' in Status_list:
			break
		time.sleep(30)

	mysettings =  init_portage_settings(session, config_id, zobcs_settings_dict)
	log_msg = "Checking categories, package, ebuilds"
	add_zobcs_logs(session, log_msg, "info", config_id)
	new_build_jobs_list = []

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
	update_repo_db(session, repo_list)

	# Close the db for the multiprocessing pool will make new ones
	# and we don't need this one for some time.

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
			new_build_jobs = pool.apply_async(update_cpv_db_pool, (mysettings, myportdb, cp, repo, zobcs_settings_dict, config_id,))
			if not new_build_jobs is None:
				new_build_jobs_list.append(new_build_jobs)
			# use this when debuging
			#update_cpv_db_pool(mysettings, myportdb, cp, repo, zobcs_settings_dict, config_id)

	#close and join the multiprocessing pools
	pool.close()
	pool.join()
	if new_build_jobs_list != []:
		add_builds_jobs (session, new_build_jobs_list, config_id)

	log_msg = "Checking categories, package and ebuilds ... done"
	add_zobcs_logs(session, log_msg, "info", config_id)

def update_db_main(session, config_id):
	# Main

	# Logging
	reader = get_conf_settings()
	zobcs_settings_dict=reader.read_zobcs_settings_all()
	log_msg = "Update db started."
	add_zobcs_logs(session, log_msg, "info", config_id)

	# Update the cpv db
	update_cpv_db(session, config_id, zobcs_settings_dict)
	log_msg = "Update db ... Done."
	add_zobcs_logs(session, log_msg, "info", config_id)
	return True
