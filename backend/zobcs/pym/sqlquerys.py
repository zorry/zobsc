from __future__ import print_function
import datetime
from zobcs.db_mapping import Configs, Logs, ConfigsMetaData, Jobs, BuildJobs, Packages, Ebuilds, Repos, Categories, \
	Uses, ConfigsEmergeOptions, EmergeOptions, HiLight, BuildLogs, BuildLogsConfig, BuildJobsUse, BuildJobsRedo, \
	HiLightCss, BuildLogsHiLight, BuildLogsEmergeOptions, BuildLogsErrors, ErrorsInfo, EmergeInfo, BuildLogsUse, \
	BuildJobsEmergeOptions
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

def get_config_id(session, config, host):
	ConfigInfo = session.query(Configs).filter_by(Config = config).filter_by(Hostname = host).one()
	return ConfigInfo.ConfigId

def add_zobcs_logs(session, log_msg, log_type, config_id):
	Add_Log = Logs(ConfigId = config_id, LogType = log_type, Msg = log_msg)
	session.add(Add_Log)
	session.commit()

def get_jobs(session, config_id):
	JobInfo = session.query(Jobs).filter_by(Status = 'Waiting').filter_by(ConfigId = config_id).order_by(Jobs.JobId).all()
	if JobInfo == []:
		return None
	return JobInfo

def update_job(session, status, job):
	job.Status = status
	session.commit()

def get_config_id_list_all(session):
	return session.query(Configs.ConfigId).all()

def get_config(session, config_id):
	ConfigInfo = session.query(Configs).filter_by(ConfigId = config_id)
	return ConfigInfo.Hostname, Config

def get_profile_checksum(session, config_id):
	return session.query(ConfigsMetaData).filter_by(ConfigId = config_id).one()

def get_packages_to_build(session, config_id):
	BuildJobsTmp = session.query(BuildJobs).filter(BuildJobs.ConfigId==config_id). \
				order_by(BuildJobs.BuildJobId)
	CurrentTime = datetime.datetime.utcnow()
	Time30Min = CurrentTime + datetime.timedelta(minutes=1)
	if session.query(BuildJobs).filter_by(ConfigId = config_id).filter(BuildJobs.BuildNow==True).all() == [] and session.query(BuildJobs).filter_by(ConfigId = config_id).all() == []:
		return None
	if BuildJobsTmp.filter(BuildJobs.BuildNow==True).first() != []:
		BuildJobsInfo, EbuildsInfo = session.query(BuildJobs, Ebuilds).filter(BuildJobs.ConfigId == config_id). \
			filter(BuildJobs.EbuildId == Ebuilds.EbuildId).order_by(BuildJobs.BuildJobId).first()
	else:
		if BuildJobsTmp.filter(BuildJobs.TimeStamp < Time30Min).first() != []:
			BuildJobsInfo, EbuildsInfo = session.query(BuildJobs, Ebuilds).filter(BuildJobs.ConfigId==config_id). \
				filter(BuildJobs.EbuildId==Ebuilds.EbuildId).order_by(BuildJobs.BuildJobId).first()
		else:
			return None
	PackagesInfo, CategoriesInfo = session.query(Packages, Categories).filter(Packages.PackageId==EbuildsInfo.PackageId).filter(Packages.CategoryId==Categories.CategoryId).one()
	ReposInfo = session.query(Repos).filter_by(RepoId = PackagesInfo.RepoId).one()
	uses={}
	for BuildJobsUseInfo, UsesInfo in session.query(BuildJobsUse, Uses).filter(BuildJobsUse.BuildJobId==BuildJobsInfo.BuildJobId).filter(BuildJobsUse.UseId==Uses.UseId).all():
		uses[UsesInfo.Flag] = BuildJobsUseInfo.Status
	if uses == {}:
		uses = None
	emerge_options_list = []
	for ConfigsEmergeOptionsInfo, EmergeOptionsInfo in session.query(ConfigsEmergeOptions, EmergeOptions). \
			filter(ConfigsEmergeOptions.ConfigId==config_id). \
			filter(ConfigsEmergeOptions.EOptionId==EmergeOptions.EmergeOptionId).all():
		emerge_options_list.append(EmergeOptionsInfo.EOption)
	build_dict={}
	build_dict['config_id'] = BuildJobsInfo.ConfigId
	build_dict['build_job_id'] = BuildJobsInfo.BuildJobId
	build_dict['ebuild_id']= EbuildsInfo.EbuildId
	build_dict['package_id'] = EbuildsInfo.PackageId
	build_dict['package'] = PackagesInfo.Package
	build_dict['category'] = CategoriesInfo.Category
	build_dict['repo'] = ReposInfo.Repo
	build_dict['removebin'] = BuildJobsInfo.RemoveBin
	build_dict['ebuild_version'] = EbuildsInfo.Version
	build_dict['checksum'] = EbuildsInfo.Checksum
	build_dict['cp'] = CategoriesInfo.Category + '/' + PackagesInfo.Package
	build_dict['cpv'] = build_dict['cp'] + '-' + EbuildsInfo.Version
	build_dict['build_useflags'] = uses
	build_dict['emerge_options'] = emerge_options_list
	return build_dict

def get_category_id(session, category):
	return session.query(Categories.CategoryId).filter_by(Category = category).filter_by(Active = True).one()[0]

def get_repo_id(session, repo):
	return session.query(Repos.RepoId).filter_by(Repo = repo).one()[0]

def get_package_id(session, categories, package, repo):
	category_id = get_category_id(session, categories)
	repo_id = get_repo_id(session, repo)
	return session.query(Packages.PackageId).filter_by(Package = package).filter_by(RepoId = repo_id).filter_by(CategoryId = category_id).one()[0]

def get_ebuild_id_db(session, build_dict):
	ebuild_id_list = []
	EbuildInfo = session.query(Ebuilds.EbuildId).filter_by(Version = build_dict['ebuild_version']).filter_by(Checksum = build_dict['checksum']).\
		filter_by(PackageId = build_dict['package_id']).filter_by(Active = True)
	if EbuildInfo.all() == []:
		return None, True
	try:
		EbuildInfo2 = EbuildInfo.one()
	except (MultipleResultsFound) as e:
		return EbuildInfo.all(), True
	return EbuildInfo2, False

def get_build_job_id(session, build_dict):
	BuildJobsIdInfo = session.query(BuildJobs.BuildJobId).filter_by(EbuildId = build_dict['ebuild_id']).filter_by(ConfigId = build_dict['config_id']).all()
	if BuildJobsIdInfo == []:
		return None
	for build_job_id in BuildJobsIdInfo:
		BuildJobsUseInfo = session.query(BuildJobsUse).filter_by(BuildJobId = build_job_id.BuildJobId).all()
		useflagsdict = {}
		if BuildJobsUseInfo == []:
			useflagsdict = None
		else:
			for x in BuildJobsUseInfo:
				useflagsdict[x.UseId] = x.Status
		if useflagsdict == build_dict['build_useflags']:
			return build_job_id.BuildJobId
	return None

def get_use_id(session, use_flag):
	try:
		UseIdInfo = session.query(Uses.UseId).filter_by(Flag = use_flag).one()
	except NoResultFound as e:
		return None
	return UseIdInfo[0]

def get_hilight_info(session):
	return session.query(HiLight).all()

def get_error_info_list(session):
	return session.query(ErrorsInfo).all()

def add_e_info(session, emerge_info, e_info_hash):
	try:
		EmergeInfoId = session.query(EmergeInfo.EInfoId).filter_by(Checksum = e_info_hash).one()
	except NoResultFound as e:
		AddEmergeInfo = EmergeInfo(Checksum = e_info_hash, EmergeInfoText = emerge_info)
		session.add(AddEmergeInfo)
		session.flush()
		EmergeInfoId = AddEmergeInfo.EInfoId
		session.commit()
		return EmergeInfoId, True
	return EmergeInfoId[0], False

def del_old_build_jobs(session, build_job_id):
	session.query(BuildJobsUse).filter(BuildJobsUse.BuildJobId == build_job_id).delete()
	session.query(BuildJobsRedo).filter(BuildJobsRedo.BuildJobId == build_job_id).delete()
	session.query(BuildJobsEmergeOptions).filter(BuildJobsEmergeOptions.BuildJobId == build_job_id).delete()
	session.query(BuildJobs).filter(BuildJobs.BuildJobId == build_job_id).delete()
	session.commit()

def add_new_buildlog(session, build_dict, build_log_dict):
	build_log_id_list = session.query(BuildLogs.BuildLogId).filter_by(EbuildId = build_dict['ebuild_id']).all()

	def add_new_hilight(log_id, build_log_dict):
		for k, hilight_tmp in sorted(build_log_dict['hilight_dict'].iteritems()):
			NewHiLight = BuildLogsHiLight(LogId = log_id, StartLine = hilight_tmp['startline'], EndLine = hilight_tmp['endline'], HiLightCssId = hilight_tmp['hilight_css_id'])
			session.add(NewHiLight)
			session.commit()

	def build_log_id_match(build_log_id_list, build_dict, build_log_dict):
		for build_log_id in build_log_id_list:
			log_hash = session.query(BuildLogs.LogHash).filter_by(BuildLogId = build_log_id[0]).one()
			use_list = session.query(BuildLogsUse).filter_by(BuildLogId = build_log_id[0]).all()
			useflagsdict = {}
			if use_list == []:
				useflagsdict = None
			else:
				for use in use_list:
					useflagsdict[use.UseId] = use.Status
			if log_hash[0] == build_log_dict['log_hash'] and build_dict['build_useflags'] == useflagsdict:
				if session.query(BuildLogsConfig).filter(BuildLogsConfig.ConfigId.in_([build_dict['config_id']])).filter_by(BuildLogId = build_log_id[0]):
					return None, True
				NewBuildLogConfig = BuildLogsConfig(BuildLogId = build_log_id[0], ConfigId = build_dict['config_id'], LogName = build_log_dict['logfilename'], EInfoId = build_log$
				session.add(NewBuildLogConfig)
				session.commit()
				return build_log_id[0], True
		return None, False

	def build_log_id_no_match(build_dict, build_log_dict):
		if build_log_dict['summary_error_list'] == []:
			NewBuildLog = BuildLogs(EbuildId = build_dict['ebuild_id'], Fail = False, SummeryText = build_log_dict['build_error'], LogHash = build_log_dict['log_hash'])
		else:
			NewBuildLog = BuildLogs(EbuildId = build_dict['ebuild_id'], Fail = True, SummeryText = build_log_dict['build_error'], LogHash = build_log_dict['log_hash'])
		session.add(NewBuildLog)
		session.flush()
		build_log_id = NewBuildLog.BuildLogId
		session.commit()
		if build_log_dict['summary_error_list'] != []:
			for error in build_log_dict['summary_error_list']:
				NewError = BuildLogsErrors(BuildLogId = build_log_id, ErrorId = error)
				session.add(NewError)
				session.commit()
		NewBuildLogConfig = BuildLogsConfig(BuildLogId = build_log_id, ConfigId = build_dict['config_id'], LogName = build_log_dict['logfilename'], EInfoId = build_log_dict['einfo_id'])
		session.add(NewBuildLogConfig)
		session.flush()
		log_id = NewBuildLogConfig.LogId
		session.commit()
		add_new_hilight(log_id, build_log_dict)
		if not build_dict['build_useflags'] is None:
			for use_id, status in  build_dict['build_useflags'].iteritems():
				NewBuildLogUse = BuildLogsUse(BuildLogId = build_log_id, UseId = use_id, Status = status)
				session.add(NewBuildLogUse)
				session.flush()
			session.commit()
		return build_log_id

	if build_dict['build_job_id'] is None and build_log_id_list == []:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		return build_log_id
	elif build_dict['build_job_id'] is None and build_log_id_list != []:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		return build_log_id
	elif not build_dict['build_job_id'] is None and build_log_id_list != []:
		build_log_id, match = build_log_id_match(build_log_id_list, build_dict, build_log_dict)
		if not match:
			build_log_id = build_log_id_no_match(build_dict, build_log_dict)
			del_old_build_jobs(session, build_dict['build_job_id'])
		return build_log_id
	elif not build_dict['build_job_id'] is None and build_log_id_list == []:
		build_log_id = build_log_id_no_match(build_dict, build_log_dict)
		del_old_build_jobs(session, build_dict['build_job_id'])
		return build_log_id

def update_fail_times(session, FailInfo):
	NewBuildJobs = session.query(BuildJobs).filter_by(BuildJobId = FailInfo.BuildJobId).one()
	NewBuildJobs.TimeStamp = datetime.datetime.utcnow()
	session.commit()

def get_fail_times(session, build_dict):
	try:
		FailInfo = session.query(BuildJobsRedo).filter_by(BuildJobId = build_dict['build_job_id']).filter_by(FailType = build_dict['type_fail']).one()
	except NoResultFound, e:
		return None
	return FailInfo

def add_fail_times(session, fail_querue_dict):
	NewBuildJobsRedo = BuildJobsRedo(BuildJobId = fail_querue_dict['build_job_id'], FailType = fail_querue_dict['fail_type'], FailTimes = fail_querue_dict['fail_times'])
	session.add(NewBuildJobsRedo)
	NewBuildJobs = session.query(BuildJobs).filter_by(BuildJobId = fail_querue_dict['build_job_id']).one()
	NewBuildJobs.TimeStamp = datetime.datetime.utcnow()
	session.commit()
