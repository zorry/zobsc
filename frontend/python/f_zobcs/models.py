# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from django.db import models

class Keywords(models.Model):
	KeywordId = models.IntegerField(primary_key=True, db_column=u'keyword_id')
	Keyword = models.CharField(max_length=45, db_column=u'keyword')
	class Meta:
		db_table = u'keywords'
	def __unicode__(self):
		return u'KeywordId : %s, Keyword : %s' % (self.KeywordId, self.Keyword)

class Setups(models.Model):
	SetupId = models.AutoField(primary_key=True, db_column=u'setup_id')
	Setup = models.CharField(max_length=100, db_column=u'setup')
	Profile = models.CharField(max_length=150, db_column=u'profile')
	class Meta:
		db_table = u'setups'
	def __unicode__(self):
		return u'SetupId : %s, Setup : %s, Profile : %s' % (self.SetupId, self.Setup, self.Profile)

class Configs(models.Model):
	ConfigId = models.AutoField(primary_key=True, db_column=u'config_id')
	HostName = models.CharField(max_length=150, db_column=u'hostname')
	SetupId = models.ForeignKey(Setups, db_column=u'setup_id')
	DefaultConfig = models.BooleanField(db_column=u'default_config')
	class Meta:
		db_table = u'configs'
	def __unicode__(self):
		return u'ConfigId : %s, HostName : %s, Config : %s , DefaultConfig : %s' % (self.ConfigId, self.HostName, self.Config, self.DefaultConfig)

class Categories(models.Model):
	CategoryId = models.IntegerField(primary_key=True, db_column=u'category_id')
	Category = models.CharField(max_length=150, db_column=u'category')
	Active = models.BooleanField(db_column=u'active')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'categories'
	def __unicode__(self):
		return u'CategoryId : %s, Category : %s, Active : %s, TimeStamp : %s,' % (self.CategoryId, self.Category, self.Active, self.TimeStamp)

class Repos(models.Model):
	RepoId = models.IntegerField(primary_key=True, db_column=u'repo_id')
	Repo = models.CharField(max_length=100, db_column=u'repo')
	class Meta:
		db_table = u'repos'
	def __unicode__(self):
		return u'RepoId : %s, Repo : %s' % (self.RepoId, self.Repo)

class Packages(models.Model):
	PackageId = models.IntegerField(primary_key=True, db_column=u'package_id')
	CategoryId = models.ForeignKey(Categories, db_column=u'category_id')
	Package = models.CharField(max_length=150, db_column=u'package')
	RepoId = models.ForeignKey(Repos, db_column=u'repo_id')
	Checksum = models.CharField(max_length=100, db_column=u'checksum')
	Active = models.BooleanField(db_column=u'active')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'packages'
	def __unicode__(self):
		return u'PackageId : %s, CategoryId : %s, Package : %s, Repos : %s, Checksum : %s, Active : %s, TimeStamp : %s' % (self.PackageId, self.CategoryId, self.Package, self.RepoId, self.Checksum, self.Active, self.TimeStamp)

class Emails(models.Model):
	EmailId = models.IntegerField(primary_key=True, db_column=u'email_id')
	Email = models.CharField(max_length=150, db_column=u'email')
	class Meta:
		db_table = u'emails'
	def __unicode__(self):
		return u'EmailId : %s, Email : %s' % (self.EmailId, self.Email)

class PackagesEmails(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	PackageId = models.ForeignKey(Packages, db_column=u'package_id')
	EmailId = models.ForeignKey(Emails, db_column=u'email_id')
	class Meta:
		db_table = u'packages_emails'
	def __unicode__(self):
		return u'PackageId : %s, EmailId : %s' % (self.PackageId, self.EmailId)

class PackagesMetadata(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	PackageId = models.ForeignKey(Packages, db_column=u'package_id')
	Checksum = models.CharField(max_length=100, db_column=u'checksum')
	class Meta:
		db_table = u'packages_metadata'
	def __unicode__(self):
		return u'PackageId : %s, Checksum : %s' % (self.PackageId, self.Checksum)

class Ebuilds(models.Model):
	EbuildId = models.IntegerField(primary_key=True, db_column=u'ebuild_id')
	PackageId = models.ForeignKey(Packages, db_column=u'package_id')
	Version = models.CharField(max_length=150, db_column=u'version')
	Checksum = models.CharField(max_length=100, db_column=u'checksum')
	Active = models.BooleanField(db_column=u'active')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'ebuilds'
	def __unicode__(self):
		return u'EbuildId : %s, PackageId : %s, Version : %s , Checksum : %s, Active : %s, TimeStamp : %s' % (self.EbuildId, self.PackageId, self.Version, self.Checksum, self.Active, self.TimeStamp)

class EmergeOptions(models.Model):
	EmergeOptionId = models.IntegerField(primary_key=True, db_column=u'eoption_id')
	EOption = models.CharField(max_length=45, db_column=u'eoption')
	class Meta:
		db_table = u'emerge_options'
	def __unicode__(self):
		return u'EmergeOptionId : %s, EOption : %s' % (self.EmergeOptionId, self.EOption)

class BuildJobs(models.Model):
	BuildJobId = models.AutoField(primary_key=True, db_column=u'build_job_id')
	EbuildId = models.ForeignKey(Ebuilds, db_column=u'ebuild_id')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	Status = models.CharField(max_length=21, db_column=u'status')
	BuildNow = models.BooleanField(db_column=u'build_now')
	RemoveBin = models.BooleanField(db_column=u'removebin')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'build_jobs'
	def __unicode__(self):
		return u'BuildJobId : %s, EbuildId : %s, ConfigId : %s , Status : %s, BuildNow : %s, RemoveBin : %s, TimeStamp : %s' % (self.BuildJobId, self.EbuildId, self.ConfigId, self.Status, self.BuildNow, self.RemoveBin, self.TimeStamp)

class BuildJobsEmergeOptions(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildJobId = models.ForeignKey(BuildJobs, db_column=u'build_job_id')
	EOptionId = models.ForeignKey(EmergeOptions, db_column=u'eoption_id')
	class Meta:
		db_table = u'build_jobs_emerge_options'
	def __unicode__(self):
		return u'BuildJobId : %s, EOptionId : %s' % (self.BuildJobId, self.EOptionId)

class BuildJobsRedo(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildJobId = models.ForeignKey(BuildJobs, db_column=u'build_job_id')
	FailTimes = models.IntegerField(db_column=u'fail_times')
	FailType = models.CharField(max_length=90, db_column=u'fail_type')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'build_jobs_redo'
	def __unicode__(self):
		return u'BuildJobId : %s, FailTimes : %s, FailType : %s ,TimeStamp : %s' % (self.BuildJobId, self.FailTimes, self.FailType, self.TimeStamp)

class Restrictions(models.Model):
	RestrictionId = models.IntegerField(primary_key=True, db_column=u'restriction_id')
	Restriction = models.CharField(max_length=150, db_column=u'restriction')
	class Meta:
		db_table = u'restrictions'
	def __unicode__(self):
		return u'RestrictionId : %s, Restriction : %s' % (self.RestrictionId, self.Restriction)
		
class Uses(models.Model):
	UseId = models.IntegerField(primary_key=True, db_column=u'use_id')
	Flag = models.CharField(max_length=150, db_column=u'flag')
	class Meta:
		db_table = u'uses'
	def __unicode__(self):
		return u'UseId : %s, Flag : %s' % (self.UseId, self.Flag)

class BuildJobsUse(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildJobId = models.ForeignKey(BuildJobs, db_column=u'build_job_id')
	UseId = models.ForeignKey(Uses, db_column=u'use_id')
	Status = models.BooleanField(db_column=u'status')
	class Meta:
		db_table = u'build_jobs_use'
	def __unicode__(self):
		return u'BuildJobId : %s, UseId : %s, Status : %s' % (self.BuildJobId, self.UseId, self.Status)

class BuildLogs(models.Model):
	BuildLogId = models.IntegerField(primary_key=True, db_column=u'build_log_id')
	EbuildId = models.ForeignKey(Ebuilds, db_column=u'ebuild_id')
	Fail = models.CharField(max_length=15, db_column=u'fail')
	SummeryText = models.TextField(db_column=u'summery_text')
	LogHash = models.CharField(max_length=100, db_column=u'log_hash')
	BugId = models.IntegerField(max_length=10, db_column=u'bug_id')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'build_logs'
	def __unicode__(self):
		return u'BuildLogId : %s, EbuildId : %s, Fail : %s ,SummeryText : %s, LogHash : %s BugId : %s, TimeStamp : %s' % (self.BuildLogId, self.EbuildId, self.Fail, self.SummeryText, self.LogHash, self.BugId, self.TimeStamp)

class EmergeInfo(models.Model):
	EInfoId = models.IntegerField(primary_key=True, db_column=u'einfo_id')
	EmergeInfoText = models.TextField(db_column=u'emerge_info_text')
	class Meta:
		db_table = u'emerge_info'
	def __unicode__(self):
		return u'EInfoId : %s, Checksum : %s, EmergeInfoText : %s' % (self.EInfoId, self.Checksum, self.EmergeInfoText)

class BuildLogsConfig(models.Model):
	LogId = models.IntegerField(primary_key=True, db_column=u'log_id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_log_id')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	EInfoId = models.ForeignKey(EmergeInfo, db_column=u'einfo_id')
	LogName = models.CharField(max_length=450, db_column=u'logname')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'build_logs_config'
	def __unicode__(self):
		return u'LogId: %s, BuildLogId : %s, ConfigId : %s, EInfoId : %s, LogName: %s, TimeStamp : %s' % (self.LogId, self.BuildLogId, self.ConfigId, self.EInfoId, self.LogName, self.TimeStamp)

class HiLightCss(models.Model):
	HiLightCssId = models.IntegerField(primary_key=True, db_column=u'hilight_css_id')
	HiLightCssName = models.CharField(max_length=30, db_column='hilight_css_name')
	HiLightCssCollor = models.CharField(max_length=30, db_column='hilight_css_collor')
	class Meta:
		db_table = u'hilight_css'
		def __unicode__(self):
			return u'HiLightCssId : %s, HiLightCssName : %s, HiLightCollor : %s' % (self.HiLightCssId, self.HiLightCssName, self.HiLightCssCollor)

class HiLight(models.Model):
	HiLightId = models.IntegerField(primary_key=True, db_column=u'hilight_id')
	HiLightSearch = models.CharField(max_length=50, db_column='hilight_search')
	HiLightSearchEnd = models.CharField(max_length=50, db_column='hilight_search_end')
	HiLightSearchPattern = models.CharField(max_length=50, db_column='hilight_search_pattern')
	HiLightCssId = models.ForeignKey(HiLightCss, db_column='hilight_css_id')
	HiLightStart = models.IntegerField(max_length=1, db_column=u'hilight_start')
	HiLightEnd = models.IntegerField(max_length=1, db_column=u'hilight_end')
	class Meta:
		db_table = u'hilight'
		def __unicode__(self):
			return u'HiLightId : %s, HiLightSearch : %s, HiLightSearchEnd : %s, HiLightSearchPattern : %s, HiLightCssId: %s, HiLightStart : %s, HiLightEnd : %s' % (self.HiLightId, self.HiLightSearch, self.HiLightSearchEnd, self.HiLightSearchPattern, self.HiLightCSS, self.HiLightStart, self.HiLightEnd)

class BuildLogsHiLight(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	LogId = models.ForeignKey(BuildLogsConfig, db_column=u'log_id')
	StartLine = models.IntegerField(max_length=10, db_column=u'start_line')
	EndLine = models.IntegerField(max_length=10, db_column=u'end_line')
	HiLightCssId = models.ForeignKey(HiLightCss, db_column=u'hilight_css_id')
	class Meta:
		db_table = u'build_logs_hilight'
	def __unicode__(self):
		return u'Id : %s, LogId : %s, StartLine : %s, EndLine : %s, HiLightId : %s' % (self.Id, self.LogId, self.StartLine, self.EndLine, self.HiLightId)

class BuildLogsEmergeOptions(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_log_id')
	EmergeOptionId = models.ForeignKey(EmergeOptions, db_column=u'eoption_id')
	class Meta:
		db_table = u'build_logs_emerge_options'
	def __unicode__(self):
		return u'BuildLogId : %s, EmergeOptionId%s' % (self.BuildLogId, self.EmergeOptionId, self.Config)

class BuildLogsQa(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_log_id')
	SummeryText = models.TextField(db_column=u'summery_text')
	class Meta:
		db_table = u'build_logs_qa'
	def __unicode__(self):
		return u'BuildLogId : %s, SummeryText : %s' % (self.BuildLogId, self.SummeryText)

class BuildLogsRepoman(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_job_id')
	SummeryText = models.TextField(db_column=u'summery_text')
	class Meta:
		db_table = u'build_logs_repoman'
	def __unicode__(self):
		return u'BuildLogId : %s, SummeryText : %s' % (self.BuildLogId, self.SummeryText)

class BuildLogsUse(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_log_id')
	UseId = models.ForeignKey(Uses, db_column=u'use_id')
	Status = models.BooleanField(max_length=15, db_column=u'status')
	class Meta:
		db_table = u'build_logs_use'
	def __unicode__(self):
		return u'BuildLogId : %s, UseId : %s, Status : %s' % (self.BuildLogId, self.UseId, self.Status)

class ConfigsEmergeOptions(models.Model):
	Id = models.IntegerField(primary_key=True, db_column=u'id')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	EmergeOptionId = models.ForeignKey(EmergeOptions, db_column=u'eoption_id')
	class Meta:
		db_table = u'configs_emerge_options'
	def __unicode__(self):
		return u'ConfigId : %s, EmergeOptionId : %s' % (self.ConfigId, self.EmergeOptionId)

class ErrorsInfo(models.Model):
	ErrorId = models.IntegerField(primary_key=True, db_column=u'error_id')
	ErrorName = models.CharField(max_length=20, db_column=u'error_name')
	ErrorSearch = models.CharField(max_length=30, db_column=u'error_search')
	class Meta:
		db_table = u'errors_info'
	def __unicode__(self):
		return u'ErrorId : %s, ErrorName : %s, ErrorSearch : %s' % (self.ErrorId, self.ErrorName, self.ErrorSearch)

class BuildLogsErrors(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	BuildLogId = models.ForeignKey(BuildLogs, db_column=u'build_log_id')
	ErrorId = models.ForeignKey(ErrorsInfo, db_column=u'error_id')
	class Meta:
		db_table = u'build_logs_errors'
	def __unicode__(self):
		return u'Id : %s, BuildLogId : %s, ErrorId : %s' % (self.Id, self.BuildLogId, self.ErrorId)

class ConfigsMetadata(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	KeywordId = models.ForeignKey(Keywords, db_column=u'keyword_id')
	MakeConfText = models.TextField(db_column=u'make_conf_text')
	Checksum = models.CharField(max_length=100, db_column=u'checksum')
	ConfigSync = models.BooleanField(db_column=u'configsync')
	Active = models.BooleanField(db_column=u'active')
	ConfigErrorText = models.TextField(db_column=u'config_error_text')
	Updateing = models.BooleanField(db_column=u'updateing')
	Status = models.CharField(max_length=21, db_column=u'status')
	Auto = models.BooleanField(db_column=u'auto')
	GitWww = models.CharField(max_length=200, db_column=u'git_www')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'configs_metadata'
	def __unicode__(self):
		return u'ConfigId : %s, KeywordId : %s ,MakeConfText : %s, Checksum : %s, ConfigSync : %s, Active : %s, ConfigErrorText : %s, Updateing : %s, Status : %s, Auto : %s, GitWww : %s, TimeStamp : %s' % (self.ConfigId, self.KeywordId, self.MakeConfText, self.Checksum, self.ConfigSync, self.Active, self.ConfigErrorText, self.Updateing, self.Status, self.Auto, self.GitWww, self.TimeStamp)

class EbuildsIuse(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	EbuildId = models.ForeignKey(Ebuilds, db_column=u'ebuild_id')
	UseId = models.ManyToManyField(Uses, db_column=u'use_id')
	Status = models.CharField(max_length=15, db_column=u'status')
	class Meta:
		db_table = u'ebuilds_iuse'
	def __unicode__(self):
		return u'EbuildId : %s, UseId : %s, Status : %s' % (self.EbuildId, self.UseId, self.Status)

class EbuildsKeywords(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	EbuildId = models.ForeignKey(Ebuilds, db_column=u'ebuild_id')
	KeywordId = models.ForeignKey(Keywords, db_column=u'keyword_id')
	Status = models.CharField(max_length=24, db_column=u'status')
	class Meta:
		db_table = u'ebuilds_keywords'
	def __unicode__(self):
		return u'EbuildId : %s, KeywordId : %s, Status : %s' % (self.EbuildId, self.KeywordId, self.Status)

class EbuildsMetadata(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	EbuildId = models.ForeignKey(Ebuilds, db_column=u'ebuild_id')
	Revision = models.CharField(max_length=30, db_column=u'revision')
	class Meta:
		db_table = u'ebuilds_metadata'
	def __unicode__(self):
		return u'EbuildId : %s, Revision : %s' % (self.EbuildId, self.Revision)

class EbuildsRestrictions(models.Model):
	Id =  models.IntegerField(primary_key=True, db_column=u'id')
	EbuildId = models.ForeignKey(Ebuilds, primary_key=True, db_column=u'ebuild_id')
	RestrictionId = models.ForeignKey(Restrictions, db_column=u'restriction_id')
	class Meta:
		db_table = u'ebuilds_restrictions'
	def __unicode__(self):
		return u'EbuildId : %s, RestrictionId : %s' % (self.EbuildId, self.RestrictionId)

class JobTypes(models.Model):
	JobTypeId = models.IntegerField(primary_key=True, db_column=u'job_type_id')
	JobType = models.CharField(max_length=60, db_column=u'type')
	class Meta:
		db_table = u'job_types'
	def __unicode__(self):
		return u'JobTypeId : %s, JobType : %s' % (self.JobTypeId, self.JobType)

class Jobs(models.Model):
	JobId = models.IntegerField(primary_key=True, db_column=u'job_id')
	JobTypeId = models.ForeignKey(JobTypes, db_column=u'job_type_id')
	Status = models.CharField(max_length=21, db_column=u'status')
	User = models.CharField(max_length=60, db_column=u'user')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	RunConfigId = models.IntegerField(db_column=u'run_config_id')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'jobs'
	def __unicode__(self):
		return u'JobId : %s, JobTypeId : %s, Status : %s ,User : %s, ConfigId : %s, RunConfigId : %s, TimeStamp : %s' % (self.JobId, self.JobTypeId, self.Status, \
			self.User, self.ConfigId, self.RunConfigId, self.TimeStamp)

class Logs(models.Model):
	LogId = models.IntegerField(primary_key=True, db_column=u'log_id')
	ConfigId = models.ForeignKey(Configs, db_column=u'config_id')
	LogType = models.CharField(max_length=15, db_column=u'log_type')
	Msg = models.TextField(db_column=u'msg')
	TimeStamp = models.DateTimeField(db_column=u'time_stamp')
	class Meta:
		db_table = u'logs'
	def __unicode__(self):
		return u'LogId : %s, ConfigId : %s, LogType : %s , Msg : %s, TimeStamp : %s' % (self.LogId, self.ConfigId, self.LogType, self.Msg, self.TimeStamp)
