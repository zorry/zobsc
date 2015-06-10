# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno
import sys
import time
import re
import git

from _emerge.main import emerge_main
from zobcs.sqlquerys import get_config_id, add_logs, get_config_all_info, get_configmetadata_info
from zobcs.readconf import read_config_settings

def git_repos_list(myportdb):
	repo_trees_list = myportdb.porttrees
	repo_dir_list = []
	for repo_dir in repo_trees_list:
		repo_dir_list.append(repo_dir)
	return repo_dir_list

def git_fetch(repo):
	repouptodate = True
	remote = git.remote.Remote(repo, 'origin')
	info_list = remote.fetch()
	local_commit = repo.commit()
	remote_commit = info_list[0].commit
	if local_commit.hexsha != remote_commit.hexsha:
		repouptodate = False
	return info_list, repouptodate

def git_merge(repo, info):
	repo.git.merge(info.commit)

def git_repo_sync_main(session):
	zobcs_settings_dict = read_config_settings()
	_hostname = zobcs_settings_dict['hostname']
	_config = zobcs_settings_dict['zobcs_config']
	config_id = get_config_id(session, _config, _hostname)
	host_config = _hostname +"/" + _config
	default_config_root = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + host_config + "/"
	mysettings = portage.config(config_root = default_config_root)
	myportdb = portage.portdbapi(mysettings=mysettings)
	GuestBusy = True
	log_msg = "Waiting for Guest to be idel"
	add_logs(session, log_msg, "info", config_id)
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
			GuestBusy = False
		else:
			time.sleep(30)
	try:
		os.remove(mysettings['PORTDIR'] + "/profiles/config/parent")
		os.rmdir(mysettings['PORTDIR'] + "/profiles/config")
	except:
		pass

	repo_cp_dict = {}
	for repo_dir in git_repos_list(myportdb):
		reponame = myportdb.getRepositoryName(repo_dir)
		attr = {}
		repo = git.Repo(repo_dir)
		info_list, repouptodate = git_fetch(repo)
		if not repouptodate:
			cp_list = []
			for diff_line in repo.git.diff('HEAD^').splitlines():
				if re.search("^diff --git.*/Manifest", diff_line):
					diff_line2 = re.split(' b/', re.sub('diff --git', '', diff_line))
					diff_line3 = re.sub(' a/', '', diff_line2[0])
					if diff_line3 == diff_line2[1] or "Manifest" in diff_line3:
						cp = re.sub('/Manifest', '', diff_line3)
						cp_list.append(cp)
					else:
						cp = re.sub('/Manifest', '', diff_line2[1])
						cp_list.append(cp)
			attr['cp_list'] = cp_list
			repo_cp_dict[reponame] = attr
			git_merge(repo, info_list[0])
		else:
			log_msg = "Repo %s is up to date" % (reponame)
			add_logs(session, log_msg, "info", config_id)
	# Need to add a config dir so we can use profiles/base for reading the tree.
	# We may allready have the dir on local repo when we sync.
	try:
		os.mkdir(mysettings['PORTDIR'] + "/profiles/config", 0o777)
		with open(mysettings['PORTDIR'] + "/profiles/config/parent", "w") as f:
			f.write("../base\n")
			f.close()
	except:
		pass
	log_msg = "Repo sync ... Done."
	add_logs(session, log_msg, "info", config_id)
	return repo_cp_dict

def git_pull(session, repo_dir), config_id):
	log_msg = "Git pull"
	add_logs(session, log_msg, "info", config_id)
	repo = git.Repo(repo_dir)
	info_list, repouptodate = git_fetch(repo)
	if not repouptodate:
		git_merge(repo, info_list[0])
	log_msg = "Git pull ... Done"
	add_logs(session, log_msg, "info", config_id)
	return True
