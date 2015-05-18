# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from __future__ import print_function
import portage
import os
import errno
import sys
import time
import re
from pygit2 import Repository, GIT_MERGE_ANALYSIS_FASTFORWARD, GIT_MERGE_ANALYSIS_NORMAL, \
        GIT_MERGE_ANALYSIS_UP_TO_DATE

from _emerge.main import emerge_main
from zobcs.sqlquerys import get_config_id, add_zobcs_logs, get_config_all_info, get_configmetadata_info
from zobcs.readconf import read_config_settings

def git_repos_list(session, mysettings, myportdb):
	repo_trees_list = myportdb.porttrees
	repo_dir_list = []
	for repo_dir in repo_trees_list:
		repo_dir_list.append(repo_dir)
	return repo_dir_list

def git_fetch(session, git_repo, config_id):
	repo = Repository(git_repo)
	remote = repo.remotes["origin"]
	remote.fetch()
	return repo

def git_merge(session, repo, config_id):
	remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
	merge_result, _ = repo.merge_analysis(remote_master_id)
	if merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
		log_msg = "Repo is up to date"
		add_zobcs_logs(session, log_msg, "info", config_id)
	elif merge_result & GIT_MERGE_ANALYSIS_FASTFORWARD:
		repo.checkout_tree(repo.get(remote_master_id))
		master_ref = repo.lookup_reference('refs/heads/master')
		master_ref.set_target(remote_master_id)
		repo.head.set_target(remote_master_id)
	elif merge_result & GIT_MERGE_ANALYSIS_NORMAL:
		repo.merge(remote_master_id)
		assert repo.index.conflicts is None, 'Conflicts, ahhhh!'
		user = repo.default_signature
		tree = repo.index.write_tree()
		commit = repo.create_commit('HEAD',
			user,
			user,
			'Merge!',
			tree,
			[repo.head.target, remote_master_id])
		repo.state_cleanup()
	else:
		raise AssertionError('Unknown merge analysis result')

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
			GuestBusy = False
		else:
			time.sleep(30)
	try:
		os.remove(mysettings['PORTDIR'] + "/profiles/config/parent")
		os.rmdir(mysettings['PORTDIR'] + "/profiles/config")
	except:
		pass

	repo_cp_dict = {}
	for repo_dir in git_repos_list(session, mysettings, myportdb):
		attr = {}
		repo = git_fetch(session, repo_dir, config_id)
		remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
		merge_result, _ = repo.merge_analysis(remote_master_id)
		if not merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
			git_merge(session, repo, config_id)
			repo_diff = repo.diff('HEAD', 'HEAD^')
			cp_list = []
			reponame = myportdb.getRepositoryName(repo_dir)
			for diff_line in repo_diff.patch.splitlines():
				if re.search("Manifest", diff_line) and re.search("^diff --git", diff_line):
					diff_line2 = re.split(' b/', re.sub('diff --git', '', diff_line))
					diff_line3 = re.sub(' a/', '', diff_line2[0])
					diff_line4 = diff_line2[1] 
					if diff_line3 == diff_line4 or "Manifest" in diff_line3:
						cp = re.sub('/Manifest', '', diff_line3)
						cp_list.append(cp)
					else:
						cp = re.sub('/Manifest', '', diff_line4)
						cp_list.append(cp)
			attr['cp_list'] = cp_list
			repo_cp_dict[reponame] = attr
		else:
			log_msg = "Repo is up to date"
			add_zobcs_logs(session, log_msg, "info", config_id)
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
	add_zobcs_logs(session, log_msg, "info", config_id)
	return repo_cp_dict

def git_pull(session, git_repo, config_id):
	log_msg = "Git pull"
	add_zobcs_logs(session, log_msg, "info", config_id)
	repo = git_fetch(session, git_repo, config_id)
	git_merge(session, repo, config_id)
	log_msg = "Git pull ... Done"
	add_zobcs_logs(session, log_msg, "info", config_id)
	return True
