from zobcs.models import *
from zobcs.forms import *
from zobcs.utils.pybugzilla import PrettyBugz
from zobcs.utils.builduseflags import config_get_use
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login
import gzip
import os

def views_main(request):
	return render(request, 'pages/main.html')

def views_categories(request):
	c_list = Categories.objects.all()
	return render(request, 'pages/categories.html', {'c_list' : c_list})

def views_packages(request, category_id):
	p_list = Packages.objects.filter(CategoryId_id = category_id)
	return render(request, 'pages/packages.html', {'p_list' : p_list})

def views_ebuilds(request, package_id):
	# For the ebuilds info.
	EbuildInfo = []
	for E in Ebuilds.objects.filter(PackageId_id = package_id):
		BL = BuildLogs.objects.filter(EbuildId = E.EbuildId)
		# FiXME: add IUSE, Keyword, Metadata and Restrictions
		# EIuse_tmp = EbuildsIuse.objects.filter(EbuildId_id__in = EbuildIdList)
		# EKeyword_tmp = EbuildsKeywords.objects.filter(EbuildId_id__in = EbuildIdList)
		EM = EbuildsMetadata.objects.get(EbuildId = E.EbuildId)
		# ERestrictions_tmp = EbuildsRestrictions.objects.filter(EbuildId_id__in = EbuildIdList)
		adict = {}
		adict['EbuildId'] = E.EbuildId
		adict['C'] = E.PackageId.CategoryId.Category
		adict['P'] = E.PackageId.Package
		adict['V'] = E.Version
		adict['R'] = E.PackageId.RepoId.Repo
		adict['RV'] = EM.Revision
		if E.Active == "True":
			adict['Active'] = True
		else:
			adict['Active'] = False
		if BL:
			adict['BuildLog'] = True
			HaveFailLog = False
			for B in BL:
				if B.Fail == "True":
					HaveFailLog = True
			if HaveFailLog:
				adict['HaveFailLog'] = HaveFailLog
			else:
				adict['HaveFailLog'] = False
		else:
			adict['BuildLog'] = False
		EbuildInfo.append(adict)
	TmpDict = { 'EI' : EbuildInfo }
	return render(request, 'pages/ebuilds.html', TmpDict)

def views_buildinfo(request, ebuild_id, buildlog_id):
	BuildLogIdList = []
	if buildlog_id == '0':
		for BL in BuildLogs.objects.filter(EbuildId__EbuildId__exact = ebuild_id):
			BuildLogIdList.append(BL.BuildLogId)
	else:
		BuildLogIdList.append(buildlog_id)
	BuildLogInfo = []
	for buildlogid in BuildLogIdList:
		B = BuildLogs.objects.get(BuildLogId = buildlogid)
		EM = EbuildsMetadata.objects.get(EbuildId = B.EbuildId.EbuildId)
		adict = {}
		if buildlog_id == '0':
			adict['OneBuildLog'] = False
		else:
			adict['OneBuildLog'] = True
		adict['BuildLogId'] = B.BuildLogId
		adict['EbuildId'] = B.EbuildId.EbuildId
		adict['C'] = B.EbuildId.PackageId.CategoryId.Category
		adict['P'] = B.EbuildId.PackageId.Package
		adict['V'] = B.EbuildId.Version
		adict['R'] = B.EbuildId.PackageId.RepoId.Repo
		adict['RV'] = EM.Revision
		if B.Fail == "True":
			adict['Fail'] = True
		else:
			adict['Fail'] = False
		adict['Summery_text'] = B.SummeryText
		config_list = []
		for BC in BuildLogsConfig.objects.filter(BuildLogId = B.BuildLogId).order_by('-TimeStamp'):
			CM = ConfigsMetadata.objects.get(ConfigId = BC.ConfigId.ConfigId)
			CEO_tmp = ConfigsEmergeOptions.objects.filter(ConfigId = BC.ConfigId.ConfigId)
			BU_tmp = BuildLogsUse.objects.filter(BuildLogId = BC.BuildLogId)
			config_eoption = []
			aadict = {}
			aadict['configid'] = BC.ConfigId.ConfigId
			aadict['hostname'] = BC.ConfigId.HostName
			aadict['config'] = BC.ConfigId.Config
			aadict['profile'] = CM.Profile
			aadict['logid'] = BC.LogId
			aadict['logname'] = BC.LogName[1:]
			aadict['emerge_info_text'] = BC.EInfoId.EmergeInfoText
			for CEO in CEO_tmp:
				config_eoption.append(CEO.EmergeOptionId.EOption)
			aadict['emerge_option'] = config_eoption
			if not BU_tmp == []:
				use_enable = []
				use_disable = []
				for BU in BU_tmp:
					if BU.Status == "True":
						use_enable.append(BU.UseId.Flag)
					else:
						use_disable.append(BU.UseId.Flag)
				if not use_enable == []:
					aadict['use_enable'] = use_enable
				if not use_disable == []:
					aadict['use_disable'] = use_disable
		        config_list.append(aadict)
                adict['BuildLog'] = config_list
		BuildLogInfo.append(adict)
	TmpDict = { 'BLI' : BuildLogInfo }
	return render(request, 'pages/buildinfo.html', TmpDict)

def views_showlog(request, log_id):
	BC = get_object_or_404(BuildLogsConfig, LogId = log_id)
	L_tmp = BuildLogsHiLight.objects.filter(LogId = log_id)
	logfile = 'logs/' + BC.ConfigId.HostName + '/' + BC.ConfigId.Config + BC.LogName
	logtext_list = open(settings.STATIC_ROOT + logfile, 'r').readlines()
	log_list = []
	add_hilight = False
	i = iter(L_tmp)
	item = i.next()
	last_item = L_tmp.order_by('-pk')[0]
	for index, text_line in enumerate(logtext_list, start=1):
		aadict = {}
		aadict['textline'] = text_line
		hilight = item.HiLightCssId.HiLightCssCollor
		if item.StartLine == index:
			add_hilight = True
		if add_hilight:
			aadict['hilight'] = hilight
		if item.EndLine == index:
			add_hilight = False
			if not last_item.Id == item.Id:
				item = i.next()
		log_list.append(aadict)
	TmpDict = {'loginfo' : BC}
	TmpDict['log_list'] = log_list
	return render(request, 'pages/showlog.html', TmpDict)

def views_newpackages(request):
	Lines = 50
	E_tmp = Ebuilds.objects.filter(Active = 'True').order_by('-TimeStamp')[:Lines]
	return render(request, 'pages/newpackages.html', { 'packages' : E_tmp })

def views_newlogs(request):
	Lines = 50
	NewLogs = []
	for BC in BuildLogsConfig.objects.order_by('-TimeStamp')[:Lines]:
		EM = EbuildsMetadata.objects.get(EbuildId = BC.BuildLogId.EbuildId.EbuildId)
		CM = ConfigsMetadata.objects.get(ConfigId = BC.ConfigId.ConfigId)
		adict = {}
		adict['BuildLogId'] = BC.BuildLogId.BuildLogId
		adict['EbuildId'] = BC.BuildLogId.EbuildId.EbuildId
		adict['C'] = BC.BuildLogId.EbuildId.PackageId.CategoryId.Category
		adict['P'] = BC.BuildLogId.EbuildId.PackageId.Package
		adict['V'] = BC.BuildLogId.EbuildId.Version
		adict['R'] = BC.BuildLogId.EbuildId.PackageId.RepoId.Repo
		adict['RV'] = EM.Revision
		if BC.BuildLogId.EbuildId.Active == "True":
			adict['Active'] = True
		else:
			adict['Active'] = False
		adict['TimeStamp'] = BC.TimeStamp
		if BC.BuildLogId.Fail == "True":
			adict['Fail'] = True
		else:
			adict['Fail'] = False
		if BC.BuildLogId.BugId == "0":
			adict['BugId'] = False
		else:
			adict['BugId'] = BC.BuildLogId.BugId
		adict['configid'] = BC.ConfigId.ConfigId
		adict['hostname'] = BC.ConfigId.HostName
		adict['config'] = BC.ConfigId.Config
		adict['profile'] = CM.Profile
		adict['logname'] = BC.LogName[1:]
		NewLogs.append(adict)
	return render(request, 'pages/newlogs.html', { 'logs' : NewLogs })

def views_newbuildjobs(request):
	Lines = 50
	BU_tmp_list = []
	BE_tmp_list = []
	B_tmp = BuildJobs.objects.order_by('-TimeStamp')[:Lines]
	for B in B_tmp:
		BU_tmp_list.append(BuildJobsUse.objects.filter(BuildJobsId_id = B.BuildJobsId))
		BE_tmp_list.append(BuildJobsEmergeOptions.objects.filter(BuildJobsId_id = B.BuildJobsId))
	TmpDict = { 'buildjobs' : B_tmp }
	TmpDict[buildjobsuse] = BU_tmp_list
	TmpDict[buildjobse] = BE_tmp_list
	return render(request, 'pages/newbuildsjobs.html', TmpDict)

def submit_to_bugzilla(form, buildlog_id):
	BC = Package(BuildLogsConfig, BuildLogId = buildlog_id)
        args = {}
        args['product'] = form.cleaned_data['Product']
        args['component'] = form.cleaned_data['Component']
        args['version'] = form.cleaned_data['Version']
        args['summary'] = form.cleaned_data['Summary']
        args['description'] = form.cleaned_data['Description']
        args['comment'] = form.cleaned_data['EmergeInfo']
        args['assigned_to'] = form.cleaned_data['AssigendTo']
	args['cc_add'] = None
	
        Bugz = PrettyBugz()
        Bugz.login()
        bugid = Bugz.post(args)
        args['bugid'] = bugid['id']
        # args['bugid'] = 496070
        Bugz.modify(args)
        
        LogFile = BC.ConfigId.HostName + '/' + BC.ConfigId.Config + BC.LogName
	LogDir = settings.STATIC_ROOT + 'logs/'
        with open(LogDir + LogFile, 'rb') as orig_file:
		with gzip.open('/tmp' + BC.LogName + '.gz', 'wb') as zipped_file:
			zipped_file.writelines(orig_file)
	args['filename'] = '/tmp' + BC.LogName + '.gz'
	args['content_type'] = 'application/gzip'
	args['comment_attach'] = 'Build log'
	Bugz.attach(args)
        
        Bugz.logout()
        return args['bugid']

def views_buildinfo_bugzilla(request, buildlog_id):
	B = get_object_or_404(BuildLogs, BuildLogId = buildlog_id)
	C = B.EbuildId.PackageId.CategoryId.Category
	P = B.EbuildId.PackageId.Package
	V = B.EbuildId.Version
	R = B.EbuildId.PackageId.RepoId.Repo
	if request.method == 'POST':
		form = BugForm(request.POST)
		if form.is_valid():
			bug = {}
			bug['id'] = submit_to_bugzilla(form, buildlog_id)
                        return HttpResponseRedirect(reverse('views_show_bug', kwargs={'bugid':bug.id,}))
	else:
		if B.Fail == 'True':
			F = get_object_or_404(BuildLogsErrors, BuildLogId = buildlog_id)
			FailText = " : " + F.ErrorId.ErrorName
		else:
			FailText = ""
		E = get_object_or_404(BuildLogsConfig, BuildLogId = buildlog_id)
		PM = get_object_or_404(PackagesMetadata, PackageId = B.EbuildId.PackageId.PackageId)
		form = BugForm()
		form.fields['Product'].initial = 'Gentoo Linux'
		form.fields['Version'].initial = 'unspecified'
		form.fields['Summary'].initial = '=' + C + '/' + P + '-' + V + '::' + R + FailText
		form.fields['Description'].initial = B.SummeryText
		form.fields['EmergeInfo'].initial = E.EInfoId.EmergeInfoText
		form.fields['AssigendTo'].initial = PM.Email

	TmpDict = { 'form': form, }
	TmpDict['B'] = B
	return render(request, 'pages/submitbug.html', TmpDict)

def views_show_bug(request, bug_id):
	return render(request, 'pages/submitbug.html', TmpDict)

def views_packagesbuild(request, ebuild_id):
	BJ = BuildJobs.objects.filter(EbuildId__EbuildId = ebuild_id)
	EM = EbuildsMetadata.objects.get(EbuildId = ebuild_id)
	BuildList = True
	if BJ == []:
		BuildList = False
	B = ebuild_id
	adict = {}
	adict['C'] = EM.EbuildId.PackageId.CategoryId.Category
	adict['P'] = EM.EbuildId.PackageId.Package
	adict['V'] = EM.EbuildId.Version
	adict['R'] = EM.EbuildId.PackageId.RepoId.Repo
	adict['RV'] = EM.Revision
	adict['Id'] = ebuild_id
	if request.method == 'POST':
		Configform = ChoiceBuildConfigSetupSelect(request.POST)
		if Configform.is_valid():
			ChoiceConfigId = Configform.cleaned_data['Config']
			return HttpResponseRedirect('/newbuild/' + ebuild_id + '/' + ChoiceConfigId + '/')
	else:
		Configform = ChoiceBuildConfigSetupSelect()
	TmpDict = { 'BuildList' : BuildList, }
	TmpDict['B'] = B
	TmpDict['Configform'] = Configform
	return render(request, 'pages/addbuild.html', TmpDict)

def views_packagesbuildnew(request, ebuild_id, config_id):
	EM = EbuildsMetadata.objects.get(EbuildId = ebuild_id)
	adict = {}
	adict['C'] = EM.EbuildId.PackageId.CategoryId.Category
	adict['P'] = EM.EbuildId.PackageId.Package
	adict['V'] = EM.EbuildId.Version
	adict['R'] = EM.EbuildId.PackageId.RepoId.Repo
	adict['RV'] = EM.Revision
	adict['Id'] = ebuild_id
	UseFlagsDict = config_get_use(ebuild_id, config_id)
	if request.method == 'POST':
		UseForm = ChoiceUseFlagsForBuild(data=request.POST, ebuild_id=ebuild_id, config_id = config_id)
		if UseForm.is_valid():
			print(UseForm.cleaned_data)
			for Use in UseForm.cleaned_data:
				if Use == "Now":
					if UseForm.cleaned_data[Use] is True:
						BuildStatus = "Now"
					else:
						BuildStatus = "Waiting"
					# NewBuildJob = BuildJobs(EbuildId = ebuild_id, ConfigId = config_id, Status = BuildStatus)
					# NewBuildJob.save()
					# NewBuildJobId = NewBuildJob.id
				else:
					UseFlag= get_object_or_404(Uses, Flag = Use)
					if UseForm.cleaned_data[Use] is True:
						UseFlagStatus = "True"
					else:
						UseFlagStatus = "False"
					# NewBuildUse = BuildJobsUse(BuildJobsId = NewBuildJob.id, UseId = UseFlag.UseId, Status = UseFlagStatus)
					# NewBuildUse.save()
			return HttpResponseRedirect('/fooo/' + ebuild_id + '/')
			# return HttpResponseRedirect('/build/' + ebuild_id + '/')
	else:
		UseForm = ChoiceUseFlagsForBuild(ebuild_id = ebuild_id, config_id = config_id)
	TmpDict = { 'PInfo' : adict, }
	TmpDict['Use'] = UseForm
	TmpDict['EbuildId'] = ebuild_id
	TmpDict['ConfigId'] = config_id
	return render(request, 'pages/addbuildjobs.html', TmpDict)
