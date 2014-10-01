from __future__ import print_function

# Queryes to add the logs
def get_config_id(connection, config, host):
	cursor = connection.cursor()
	sqlQ = 'SELECT config_id FROM configs WHERE config = %s AND hostname= %s'
	cursor.execute(sqlQ,(config, host,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def add_zobcs_logs(connection, log_msg, log_type, config):
	cursor = connection.cursor()
	sqlQ = 'INSERT INTO logs (config_id, log_type, msg) VALUES ( %s, %s, %s )'
	cursor.execute(sqlQ, (config, log_type, log_msg))
	connection.commit()
	cursor.close()

# Queryes to handel the jobs table
def get_jobs_id(connection, config_id):
	cursor = connection.cursor()
	sqlQ = "SELECT job_id FROM jobs WHERE status = 'Waiting' AND config_id = %s"
	cursor.execute(sqlQ, (config_id,))
	entries = cursor.fetchall()
	cursor.close()
	if entries is None:
		return None
	jobs_id = []
	for job_id in entries:
		jobs_id.append(job_id[0])
	return sorted(jobs_id)

def get_job(connection, job_id):
	cursor = connection.cursor()
	sqlQ ='SELECT job_type_id, run_config_id FROM jobs WHERE job_id = %s'
	cursor.execute(sqlQ, (job_id,))
	entries = cursor.fetchone()
	cursor.close()
	job = entries[0]
	config_id = entries[1]
	return job, config_id

def get_job_type(connection, job_type_id):
	cursor = connection.cursor()
	sqlQ = 'SELECT type FROM job_types WHERE job_type_id = %s'
	cursor.execute(sqlQ, (job_type_id,))
	entries = cursor.fetchone()
	cursor.close()
	return entries[0]

def update_job_list(connection, status, job_id):
	cursor = connection.cursor()
	sqlQ = 'UPDATE  jobs SET status = %s WHERE job_id = %s'
	cursor.execute(sqlQ, (status, job_id,))
	connection.commit()
	cursor.close()

# Queryes to handel the configs* tables
def get_config_list_all(connection):
	cursor = connection.cursor()
	sqlQ = 'SELECT config_id FROM configs'
	cursor.execute(sqlQ)
	entries = cursor.fetchall()
	cursor.close()
	config_id_list = []
	for config_id in entries:
		config_id_list.append(config_id[0])
	return config_id_list

def get_config(connection, config_id):
	cursor = connection.cursor()
	sqlQ ='SELECT hostname, config FROM configs WHERE config_id = %s'
	cursor.execute(sqlQ, (config_id,))
	hostname, config = cursor.fetchone()
	cursor.close()
	return hostname, config

def update_make_conf(connection, configsDict):
	cursor = connection.cursor()
	sqlQ = 'UPDATE configs_metadata SET checksum = %s, make_conf_text = %s, active = %s, config_error_text = %s WHERE config_id = %s'
	for k, v in configsDict.iteritems():
		cursor.execute(sqlQ, (v['make_conf_checksum_tree'], v['make_conf_text'], v['active'], v['config_error'], k,))
	connection.commit()
	cursor.close()

def get_default_config(connection):
	cursor = connection.cursor()
	sqlQ = "SELECT hostname, config FROM configs WHERE default_config = 'True'"
	cursor.execute(sqlQ)
	hostname, config = cursor.fetchone()
	cursor.close()
	return hostname, config

def get_repo_id(connection, repo):
	cursor = connection.cursor()
	sqlQ ='SELECT repo_id FROM repos WHERE repo = %s'
	cursor.execute(sqlQ, (repo,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def update_repo_db(connection, repo_list):
	cursor = connection.cursor()
	sqlQ = 'INSERT INTO repos (repo) VALUES ( %s )'
	for repo in repo_list:
		repo_id = get_repo_id(connection, repo)
		if repo_id is None:
			cursor.execute(sqlQ, (repo,))
	connection.commit()
	cursor.close()

def get_category_id(connection, categories):
	cursor = connection.cursor()
	sqlQ = "SELECT category_id FROM categories WHERE category = %s AND active = 'True'"
	cursor.execute(sqlQ, (categories,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]
	
def update_categories_db(connection, categories):
	cursor = connection.cursor()
	sqlQ = 'INSERT INTO categories (category) VALUES ( %s )'
	category_id = get_category_id(connection, categories)
	if category_id is None:
		cursor.execute(sqlQ, (categories,))
	connection.commit()
	cursor.close()

def get_package_id(connection, categories, package, repo):
	cursor = connection.cursor()
	sqlQ ='SELECT package_id FROM packages WHERE category_id = %s AND package = %s AND repo_id = %s'
	category_id = get_category_id(connection, categories)
	repo_id = get_repo_id(connection, repo)
	cursor.execute(sqlQ, (category_id, package, repo_id,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def add_new_manifest_sql(connection, cp, repo):
	cursor = connection.cursor()
	sqlQ1 = "INSERT INTO packages (category_id, package, repo_id, checksum, active) VALUES (%s, %s, %s, '0', 'True')"
	sqlQ2 = 'SELECT LAST_INSERT_ID()'
	element = cp.split('/')
	categories = element[0]
	package = element[1]
	repo_id = get_repo_id(connection, repo)
	category_id = get_category_id(connection, categories)
	cursor.execute(sqlQ1, (category_id, package, repo_id, ))
	cursor.execute(sqlQ2)
	package_id = cursor.fetchone()[0]
	connection.commit()
	cursor.close()
	return package_id

def get_package_metadata_sql(connection, package_id):
	cursor = connection.cursor()
	sqlQ ='SELECT checksum FROM packages_metadata WHERE package_id = %s'
	cursor.execute(sqlQ, (package_id,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]
	return None

def update_package_metadata(connection, package_metadataDict):
	cursor = connection.cursor()
	sqlQ1 ='SELECT package_id FROM packages_metadata WHERE package_id = %s'
	sqlQ2 = 'UPDATE packages_metadata SET checksum = %s, email = %s, active = %s WHERE package_id = %s'
	sqlQ3 = 'INSERT INTO packages_metadata (checksum, email, package_id) VALUES ( %s, %s, %s )'
	for k, v in package_metadataDict.iteritems():
		cursor.execute(sqlQ1, (k,))
		entries = cursor.fetchone()
		if not entries is None:
			cursor.execute(sqlQ2, (v['metadata_xml_checksum'], v['metadata_xml_email'][0], k,))
		else:
			cursor.execute(sqlQ3, (v['metadata_xml_checksum'], v['metadata_xml_email'][0], k,))
	connection.commit()
	cursor.close()
	
def get_restriction_id(connection, restriction):
	cursor = connection.cursor()
	sqlQ ='SELECT restriction_id FROM restrictions WHERE restriction = %s'
	cursor.execute(sqlQ, (restriction,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def get_use_id(connection, use_flag):
	cursor = connection.cursor()
	sqlQ ='SELECT use_id FROM uses WHERE flag = %s'
	cursor.execute(sqlQ, (use_flag,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def get_keyword_id(connection, keyword):
	cursor = connection.cursor()
	sqlQ ='SELECT keyword_id FROM keywords WHERE keyword = %s'
	cursor.execute(sqlQ, (keyword,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def add_new_ebuild_metadata_sql(connection, ebuild_id, keywords, restrictions, iuse_list):
	cursor = connection.cursor()
	sqlQ1 = 'INSERT INTO keywords (keyword) VALUES ( %s )'
	sqlQ3 = 'INSERT INTO restrictions (restriction) VALUES ( %s )'
	sqlQ4 = 'INSERT INTO ebuilds_restrictions (ebuild_id, restriction_id) VALUES ( %s, %s )'
	sqlQ5 = 'INSERT INTO uses (flag) VALUES ( %s )'
	sqlQ6 = 'INSERT INTO ebuilds_iuse (ebuild_id, use_id, status) VALUES ( %s, %s, %s)'
	sqlQ7 = 'INSERT INTO ebuilds_keywords (ebuild_id, keyword_id, status) VALUES ( %s, %s, %s)'
	sqlQ8 = 'SELECT LAST_INSERT_ID()'
	# FIXME restriction need some filter as iuse and keyword have.
	for restriction in restrictions:
		restriction_id = get_restriction_id(connection, restriction)
		if restriction_id is None:
			cursor.execute(sqlQ3, (restriction,))
			cursor.execute(sqlQ8)
			restriction_id = cursor.fetchone()[0]
		cursor.execute(sqlQ4, (ebuild_id, restriction_id,))
	for iuse in iuse_list:
		set_iuse = 'False'
		if iuse[0] in ["+"]:
			iuse = iuse[1:]
			set_iuse = 'True'
		elif iuse[0] in ["-"]:
			iuse = iuse[1:]
		use_id = get_use_id(connection, iuse)
		if use_id is None:
			cursor.execute(sqlQ5, (iuse,))
			cursor.execute(sqlQ8)
			use_id = cursor.fetchone()[0]
		cursor.execute(sqlQ6, (ebuild_id, use_id, set_iuse,))
	for keyword in keywords:
		set_keyword = 'Stable'
		if keyword[0] in ["~"]:
			keyword = keyword[1:]
			set_keyword = 'Unstable'
		elif keyword[0] in ["-"]:
			keyword = keyword[1:]
			set_keyword = 'Negative'
		keyword_id = get_keyword_id(connection, keyword)
		if keyword_id is None:
			cursor.execute(sqlQ1, (keyword,))
			cursor.execute(sqlQ8)
			keyword_id = cursor.fetchone()[0]
		cursor.execute(sqlQ7, (ebuild_id, keyword_id, set_keyword,))
	connection.commit()
	cursor.close()

def add_new_ebuild_sql(connection, package_id, ebuildDict):
	cursor = connection.cursor()
	sqlQ1 = "INSERT INTO ebuilds (package_id, version, checksum, active) VALUES (%s, %s, %s, 'True')"
	sqlQ2 = 'SELECT LAST_INSERT_ID()'
	sqlQ3 = "INSERT INTO ebuilds_metadata (ebuild_id, revision) VALUES (%s, %s)"
	ebuild_id_list = []
	for k, v in ebuildDict.iteritems():
		cursor.execute(sqlQ1, (package_id, v['ebuild_version_tree'], v['ebuild_version_checksum_tree'],))
		cursor.execute(sqlQ2)
		ebuild_id = cursor.fetchone()[0]
		cursor.execute(sqlQ3, (ebuild_id, v['ebuild_version_revision_tree'],))
		ebuild_id_list.append(ebuild_id)
		restrictions = []
		keywords = []
		iuse = []
		for i in v['ebuild_version_metadata_tree'][4].split():
			restrictions.append(i)
		for i in v['ebuild_version_metadata_tree'][8].split():
			keywords.append(i)
		for i in v['ebuild_version_metadata_tree'][10].split():
			iuse.append(i)
		add_new_ebuild_metadata_sql(connection, ebuild_id, keywords, restrictions, iuse)
	connection.commit()
	cursor.close()
	return ebuild_id_list

def get_config_id_list(connection):
	cursor = connection.cursor()
	sqlQ = "SELECT configs.config_id FROM configs, configs_metadata WHERE configs.default_config = 'False' AND configs_metadata.active = 'True' AND configs.config_id = configs_metadata.config_id"
	cursor.execute(sqlQ)
	entries = cursor.fetchall()
	cursor.close()
	if entries == ():
		return None
	else:
		config_id_list = []
	for config_id in entries:
		config_id_list.append(config_id[0])
	return config_id_list

def add_new_build_job(connection, ebuild_id, config_id, use_flagsDict):
	cursor = connection.cursor()
	sqlQ1 = 'INSERT INTO build_jobs (ebuild_id, config_id) VALUES (%s, %s)'
	sqlQ2 = 'INSERT INTO build_jobs_use (build_job_id, use_id, status) VALUES (%s, %s, %s)'
	sqlQ3 = 'SELECT LAST_INSERT_ID()'
	sqlQ4 = 'INSERT INTO uses (flag) VALUES ( %s )'
	cursor.execute(sqlQ1, (ebuild_id, config_id,))
	cursor.execute(sqlQ3)
	build_job_id = cursor.fetchone()[0]
	for k, v in use_flagsDict.iteritems():
		use_id = get_use_id(connection, k)
		if use_id is None:
			cursor.execute(sqlQ4, (k,))
			cursor.execute(sqlQ3)
			use_id = cursor.fetchone()[0]
		cursor.execute(sqlQ2, (build_job_id, use_id, v,))
	connection.commit()
	cursor.close()

def get_manifest_db(connection, package_id):
	cursor = connection.cursor()
	sqlQ = 'SELECT checksum FROM packages WHERE package_id = %s'
	cursor.execute(sqlQ, (package_id,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def get_category(connection, category_id):
	cursor = connection.cursor()
	sqlQ = "SELECT category FROM categories WHERE category_id = %s AND active = 'True'"
	cursor.execute(sqlQ, (category_id,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def get_cp_from_package_id(connection, package_id):
	cursor = connection.cursor()
	sqlQ = "SELECT category_id, package FROM packages WHERE package_id = %s"
	cursor.execute(sqlQ, (package_id,))
	entries = cursor.fetchone()
	cursor.close()
	category_id = entries[0]
	package = entries[1]
	category = get_category(connection, category_id)
	cp = category + '/' + package
	return cp

def get_cp_repo_from_package_id(connection, package_id):
	cursor =connection.cursor()
	sqlQ = 'SELECT repos.repo FROM repos, packages WHERE repos.repo_id = packages.repo_id AND packages.package_id = %s'
	cp = get_cp_from_package_id(connection, package_id)
	cursor.execute(sqlQ, (package_id,))
	repo = cursor.fetchone()
	cursor.close()
	return cp, repo[0]

def get_ebuild_checksum(connection, package_id, ebuild_version_tree):
	cursor = connection.cursor()
	sqlQ = "SELECT checksum FROM ebuilds WHERE package_id = %s AND version = %s AND active = 'True'"
	cursor.execute(sqlQ, (package_id, ebuild_version_tree))
	entries = cursor.fetchall()
	cursor.close()
	if entries == []:
		return None
	checksums = []
	for i in entries:
		checksums.append(i[0])
	return checksums

def get_ebuild_id_list(connection, package_id):
	cursor = connection.cursor()
	sqlQ = "SELECT ebuild_id FROM ebuilds WHERE package_id = %s AND active = 'True'"
	cursor.execute(sqlQ, (package_id,))
	entries = cursor.fetchall()
	cursor.close()
	ebuilds_id = []
	for i in entries:
		ebuilds_id.append(i[0])
	return ebuilds_id

def get_ebuild_id_db(connection, checksum, package_id):
	cursor = connection.cursor()
	sqlQ = "SELECT ebuild_id FROM ebuilds WHERE package_id = %s AND checksum = %s"
	cursor.execute(sqlQ, (package_id, checksum,))
	entries = cursor.fetchall()
	cursor.close()
	ebuilds_id = []
	for i in entries:
		ebuilds_id.append(i[0])
	return ebuilds_id

def del_old_build_jobs(connection, build_job_id):
	cursor = connection.cursor()
	sqlQ1 = 'DELETE FROM build_jobs_use WHERE build_job_id = %s'
	sqlQ2 = 'DELETE FROM build_jobs_redo WHERE build_job_id  = %s'
	sqlQ3 = 'DELETE FROM build_jobs_emerge_options WHERE build_job_id = %s'
	sqlQ4 = 'DELETE FROM build_jobs WHERE build_job_id  = %s'
	cursor.execute(sqlQ1, (build_job_id,))
	cursor.execute(sqlQ2, (build_job_id,))
	cursor.execute(sqlQ3, (build_job_id,))
	cursor.execute(sqlQ4, (build_job_id,))
	connection.commit()
	cursor.close()

def add_old_ebuild(connection, package_id, old_ebuild_list):
	cursor = connection.cursor()
	sqlQ1 = "UPDATE ebuilds SET active = 'False' WHERE ebuild_id = %s"
	sqlQ3 = "SELECT build_job_id FROM build_jobs WHERE ebuild_id = %s"
	for ebuild_id in  old_ebuild_list:
		cursor.execute(sqlQ3, (ebuild_id),)
		build_job_id_list = cursor.fetchall()
		if build_job_id_list is not None:
			for build_job_id in build_job_id_list:
				del_old_build_jobs(connection, build_job_id[0])
		cursor.execute(sqlQ1, (ebuild_id,))
	connection.commit()
	cursor.close()

def update_manifest_sql(connection, package_id, manifest_checksum_tree):
	cursor = connection.cursor()
	sqlQ = 'UPDATE packages SET checksum = %s WHERE package_id = %s'
	cursor.execute(sqlQ, (manifest_checksum_tree, package_id,))
	connection.commit()
	cursor.close()

def get_build_jobs_id_list_config(connection, config_id):
	cursor = connection.cursor()
	sqlQ = 'SELECT build_job_id FROM build_jobs WHERE config_id = %s'
	cursor.execute(sqlQ,  (config_id,))
	entries = cursor.fetchall()
	cursor.close()
	build_jobs_id_list = []
	if not entries == []:
		for build_job_id_id in entries:
			build_jobs_id_list.append(build_job_id[0])
	else:
			build_log_id_list = None
	return build_jobs_id_list

def get_profile_checksum(connection, config_id):
	cursor = connection.cursor()
	sqlQ = "SELECT checksum FROM configs_metadata WHERE active = 'True' AND config_id = %s AND auto = 'True'"
	cursor.execute(sqlQ, (config_id,))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		return entries[0]

def get_packages_to_build(connection, config_id):
	cursor =connection.cursor()
	sqlQ1 = "SELECT build_jobs.build_job_id, build_jobs.ebuild_id, ebuilds.package_id FROM build_jobs, ebuilds WHERE build_jobs.config_id = %s AND build_jobs.ebuild_id = ebuilds.ebuild_id AND ebuilds.active = 'True' AND TIMESTAMPDIFF(HOUR, build_jobs.time_stamp, NOW()) > 1 ORDER BY build_jobs.build_job_id LIMIT 1"
	sqlQ2 = 'SELECT version, checksum FROM ebuilds WHERE ebuild_id = %s'
	sqlQ3 = 'SELECT uses.flag, build_jobs_use.status FROM build_jobs_use, uses WHERE build_jobs_use.build_job_id = %s AND build_jobs_use.use_id = uses.use_id'
	sqlQ4 = "SELECT build_jobs.build_job_id, build_jobs.ebuild_id, ebuilds.package_id FROM build_jobs, ebuilds WHERE build_jobs.config_id = %s AND build_jobs.ebuild_id = ebuilds.ebuild_id AND ebuilds.active = 'True' AND build_jobs.status = 'Now' LIMIT 1"
	sqlQ5 = 'SELECT emerge_options.eoption FROM configs_emerge_options, emerge_options WHERE configs_emerge_options.config_id = %s AND configs_emerge_options.eoption_id = emerge_options.eoption_id'
	sqlQ6 = 'SELECT emerge_options.eoption FROM build_jobs_emerge_options, emerge_options WHERE build_jobs_emerge_options.build_job_id = %s AND build_jobs_emerge_options.eoption_id = emerge_options.eoption_id'
	cursor.execute(sqlQ4, (config_id,))
	entries = cursor.fetchone()
	if entries is None:
		cursor.execute(sqlQ1, (config_id,))
		entries = cursor.fetchone()
	if entries is None:
		cursor.close()
		return
	build_dict={}
	build_dict['config_id'] = config_id
	build_dict['build_job_id'] = entries[0]
	build_dict['ebuild_id']= entries[1]
	build_dict['package_id'] = entries[2]
	cursor.execute(sqlQ2, (entries[1],))
	entries = cursor.fetchone()
	build_dict['ebuild_version'] = entries[0]
	build_dict['checksum']=entries[1]
	#add a enabled and disabled list to the objects in the item list
	cursor.execute(sqlQ3, (build_dict['build_job_id'],))
	uses={}
	for row in cursor.fetchall():
		uses[ row[0] ] = row[1]
	build_dict['build_useflags']=uses
	emerge_options_list = []
	cursor.execute(sqlQ5, (config_id,))
	entries = cursor.fetchall()
	for option in entries:
		emerge_options_list.append(option[0])
	cursor.execute(sqlQ6, (build_dict['build_job_id'],))
	entries = cursor.fetchall()
	cursor.close()
	for option in entries:
		emerge_options_list.append(option[0])
	if emerge_options_list == []:
		emerge_options_list = None
	build_dict['emerge_options'] = emerge_options_list
	return build_dict

def update_fail_times(connection, fail_querue_dict):
	cursor = connection.cursor()
	sqlQ1 = 'UPDATE build_jobs_redo SET fail_times = %s WHERE build_job_id = %s AND fail_type = %s'
	sqlQ2 = 'UPDATE build_jobs SET time_stamp = NOW() WHERE build_job_id = %s'
	cursor.execute(sqlQ1, (fail_querue_dict['fail_times'], fail_querue_dict['build_job_id'], fail_querue_dict['fail_type'],))
	cursor.execute(sqlQ2, (fail_querue_dict['build_job_id'],))
	connection.commit()
	cursor.close()

def get_fail_querue_dict(connection, build_dict):
	cursor = connection.cursor()
	fail_querue_dict = {}
	sqlQ = 'SELECT fail_times FROM build_jobs_redo WHERE build_job_id = %s AND fail_type = %s'
	cursor.execute(sqlQ, (build_dict['build_job_id'], build_dict['type_fail'],))
	entries = cursor.fetchone()
	cursor.close()
	if not entries is None:
		fail_querue_dict['fail_times'] = entries[0]
		return fail_querue_dict

def add_fail_querue_dict(connection, fail_querue_dict):
	cursor = connection.cursor()
	sqlQ1 = 'INSERT INTO build_jobs_redo (build_job_id, fail_type, fail_times) VALUES ( %s, %s, %s)'
	sqlQ2 = 'UPDATE build_jobs SET time_stamp = NOW() WHERE build_job_id = %s'
	cursor.execute(sqlQ1, (fail_querue_dict['build_job_id'],fail_querue_dict['fail_type'], fail_querue_dict['fail_times']))
	cursor.execute(sqlQ2, (fail_querue_dict['build_job_id'],))
	connection.commit()
	cursor.close()

def get_ebuild_id_db_checksum(connection, build_dict):
	cursor = connection.cursor()
	sqlQ = "SELECT ebuild_id FROM ebuilds WHERE version = %s AND checksum = %s AND package_id = %s AND active = 'True'"
	cursor.execute(sqlQ, (build_dict['ebuild_version'], build_dict['checksum'], build_dict['package_id']))
	ebuild_id_list = []
	entries = cursor.fetchall()
	cursor.close()
	if entries != []:
		for ebuild_id in entries:
			ebuild_id_list.append(ebuild_id[0])
		return ebuild_id_list


def get_build_job_id(connection, build_dict):
	cursor = connection.cursor()
	sqlQ1 = 'SELECT build_job_id FROM build_jobs WHERE ebuild_id = %s AND config_id = %s'
	sqlQ2 = 'SELECT use_id, status FROM build_jobs_use WHERE build_job_id = %s'
	cursor.execute(sqlQ1, (build_dict['ebuild_id'], build_dict['config_id']))
	build_job_id_list = cursor.fetchall()
	if build_job_id_list == []:
		cursor.close()
		return
	for build_job_id in build_job_id_list:
		cursor.execute(sqlQ2, (build_job_id[0],))
		entries = cursor.fetchall()
		useflagsdict = {}
		if entries == []:
			useflagsdict = None
		else:
			for x in entries:
				useflagsdict[x[0]] = x[1]
		if useflagsdict == build_dict['build_useflags']:
			cursor.close()
			return build_job_id[0]
	cursor.close()

def get_hilight_info(connection):
	cursor = connection.cursor()
	sqlQ = 'SELECT hilight_search, hilight_search_end, hilight_css_id, hilight_start, hilight_end FROM hilight'
	hilight = []
	cursor.execute(sqlQ)
	entries = cursor.fetchall()
	cursor.close()
	for i in entries:
		aadict = {}
		aadict['hilight_search'] = i[0]
		if i[1] == "":
			aadict['hilight_search_end'] = i[1]
		else:
			aadict['hilight_search_end'] = i[1]
		aadict['hilight_css_id'] = i[2]
		aadict['hilight_start'] = i[3]
		aadict['hilight_end'] = i[4]
		hilight.append(aadict)
	return hilight

def get_error_info_list(connection):
	cursor = connection.cursor()
	sqlQ = 'SELECT error_id, error_name, error_search FROM errors_info'
	cursor.execute(sqlQ)
	entries = cursor.fetchall()
	cursor.close()
	error_info = []
	for i in entries:
		aadict = {}
		aadict['error_id'] = i[0]
		aadict['error_name'] = i[1]
		aadict['error_search'] = i[2]
		error_info.append(aadict)
	return error_info

def add_new_buildlog(connection, build_dict, build_log_dict):
	cursor = connection.cursor()
	sqlQ1 = 'SELECT build_log_id FROM build_logs WHERE ebuild_id = %s'
	sqlQ2 ="INSERT INTO build_logs (ebuild_id, summery_text, log_hash) VALUES (%s, 'FF', 'FF')"
	sqlQ3 = "UPDATE build_logs SET fail = 'True' WHERE build_log_id = %s"
	sqlQ4 = 'INSERT INTO build_logs_config (build_log_id, config_id, logname) VALUES (%s, %s, %s)'
	sqlQ6 = 'INSERT INTO build_logs_use (build_log_id, use_id, status) VALUES (%s, %s, %s)'
	sqlQ7 = 'SELECT log_hash FROM build_logs WHERE build_log_id = %s'
	sqlQ8 = 'SELECT use_id, status FROM build_logs_use WHERE build_log_id = %s'
	sqlQ9 = 'SELECT config_id FROM build_logs_config WHERE build_log_id = %s'
	sqlQ10 = "UPDATE build_logs SET summery_text = %s, log_hash = %s WHERE build_log_id = %s"
	sqlQ11 = 'SELECT LAST_INSERT_ID()'
	sqlQ12 = 'INSERT INTO build_logs_hilight (log_id, start_line, end_line, hilight_css_id) VALUES (%s, %s, %s, %s)'
	sqlQ13 = 'INSERT INTO build_logs_errors ( build_log_id, error_id) VALUES (%s, %s)'
	build_log_id_list = []
	cursor.execute(sqlQ1, (build_dict['ebuild_id'],))
	entries = cursor.fetchall()
	if not entries == []:
		for build_log_id in entries:
			build_log_id_list.append(build_log_id[0])
	else:
		build_log_id_list = None
	
	def add_new_hilight(build_log_id, build_log_dict):
		for k, hilight_tmp in sorted(build_log_dict['hilight_dict'].iteritems()):
			cursor.execute(sqlQ12, (build_log_id,hilight_tmp['startline'],  hilight_tmp['endline'], hilight_tmp['hilight_css_id'],))

	def build_log_id_match(build_log_id_list, build_dict, build_log_dict):
		for build_log_id in build_log_id_list:
			cursor.execute(sqlQ7, (build_log_id,))
			log_hash = cursor.fetchone()
			cursor.execute(sqlQ8, (build_log_id,))
			entries = cursor.fetchall()
			useflagsdict = {}
			if entries == []:
				useflagsdict = None
			else:
				for x in entries:
					useflagsdict[x[0]] = x[1]
			if log_hash[0] == build_log_dict['log_hash'] and build_dict['build_useflags'] == useflagsdict:
				cursor.execute(sqlQ9, (build_log_id,))
				config_id_list = []
				for config_id in cursor.fetchall():
					config_id_list.append(config_id[0])
				if build_dict['config_id'] in config_id_list:
					return None, True
				cursor.execute(sqlQ4, (build_log_id, build_dict['config_id'], build_log_dict['logfilename'],))
				return build_log_id, True
		return None, False

	def build_log_id_no_match(build_dict, build_log_dict):
		cursor.execute(sqlQ2, (build_dict['ebuild_id'],))
		cursor.execute(sqlQ11)
		build_log_id = cursor.fetchone()[0]
		if build_log_dict['summary_error_list'] != []:
			cursor.execute(sqlQ3, (build_log_id,))
			for error in build_log_dict['summary_error_list']:
				cursor.execute(sqlQ13, (build_log_id, error,))
		cursor.execute(sqlQ10, (build_log_dict['build_error'], build_log_dict['log_hash'], build_log_id,))
		add_new_hilight(build_log_id, build_log_dict)
		cursor.execute(sqlQ4, (build_log_id, build_dict['config_id'], build_log_dict['logfilename'],))
		if not build_dict['build_useflags'] is None:
			for use_id, status in  build_dict['build_useflags'].iteritems():
				cursor.execute(sqlQ6, (build_log_id, use_id, status))
		return build_log_id

	if build_dict['build_job_id'] is None and build_log_id_list is None:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		cursor.close()
		return build_log_id
	elif build_dict['build_job_id'] is None and not build_log_id_list is None:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		cursor.close()
		return build_log_id
	elif not build_dict['build_job_id'] is None and not build_log_id_list is None:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
			del_old_build_jobs(connection, build_dict['build_job_id'])
		cursor.close()
		return build_log_id
	elif not build_dict['build_job_id'] is None and build_log_id_list is None:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		del_old_build_jobs(connection, build_dict['build_job_id'])
		cursor.close()
		return build_log_id

def add_e_info(connection, log_id, emerge_info, e_info_hash):
	cursor = connection.cursor()
	sqlQ1 = 'SELECT einfo_id FROM emerge_info WHERE checksum = %s'
	sqlQ2 = 'UPDATE build_logs SET einfo_id = %s WHERE build_log_id = %s'
	sqlQ3 ='INSERT INTO emerge_info (checksum, emerge_info_text) VALUES (%s, %s)'
	sqlQ4 = 'SELECT LAST_INSERT_ID()'
	cursor.execute(sqlQ1, (e_info_hash,))
	entries = cursor.fetchall()
	if entries != []:
		cursor.execute(sqlQ2, (entries[0],))
		connection.commit()
		cursor.close()
		return None
	cursor.execute(sqlQ3, (e_info_hash, emerge_info,))
	cursor.execute(sqlQ4)
	entries = cursor.fetchall()
	cursor.execute(sqlQ2, (entries[0],))
	connection.commit()
	cursor.close()
	return entries[0]

