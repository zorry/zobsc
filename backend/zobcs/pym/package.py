from __future__ import print_function
import portage
from portage.xml.metadata import MetaDataXML
from zobcs.flags import zobcs_use_flags
from zobcs.manifest import zobcs_manifest
from zobcs.text import get_ebuild_cvs_revision
from zobcs.flags import zobcs_use_flags
from zobcs.mysql_querys import get_config, get_config_id, add_zobcs_logs, get_default_config, \
	add_new_build_job, get_config_id_list, update_manifest_sql, add_new_manifest_sql, \
	add_new_ebuild_sql, get_ebuild_id_db, add_old_ebuild, get_ebuild_id_list, \
	get_ebuild_checksum, get_manifest_db, get_cp_repo_from_package_id, \
	get_cp_from_package_id, get_package_metadata_sql, update_package_metadata
from zobcs.readconf import get_conf_settings
reader=get_conf_settings()
zobcs_settings_dict=reader.read_zobcs_settings_all()
_config = zobcs_settings_dict['zobcs_config']
_hostname =zobcs_settings_dict['hostname']

class zobcs_package(object):

	def __init__(self, conn, mysettings, myportdb):
		self._conn = conn
		self._mysettings = mysettings
		self._myportdb = myportdb
		self._config_id = get_config_id(conn, _config, _hostname)

	def change_config(self, host_config):
		# Change config_root  config_setup = table config
		my_new_setup = "/var/cache/zobcs/" + zobcs_settings_dict['zobcs_gitreponame'] + "/" + host_config + "/"
		mysettings_setup = portage.config(config_root = my_new_setup)
		return mysettings_setup

	def config_match_ebuild(self, cp, config_id_list):
		config_cpv_listDict ={}
		if config_id_list == []:
			return config_cpv_listDict
		for config_id in config_id_list:

			# Change config/setup
			hostname, config = get_config(self._conn, config_id)
			mysettings_setup = self.change_config(hostname + "/" + config)
			myportdb_setup = portage.portdbapi(mysettings=mysettings_setup)

			# Get the latest cpv from portage with the config that we can build
			build_cpv = myportdb_setup.xmatch('bestmatch-visible', cp)

			# Check if could get cpv from portage and add it to the config_cpv_listDict.
			if build_cpv != "":

				# Get the iuse and use flags for that config/setup and cpv
				init_useflags = zobcs_use_flags(mysettings_setup, myportdb_setup, build_cpv)
				iuse_flags_list, final_use_list = init_useflags.get_flags()
				iuse_flags_list2 = []
				for iuse_line in iuse_flags_list:
					iuse_flags_list2.append( init_useflags.reduce_flag(iuse_line))

				# Dict the needed info
				attDict = {}
				attDict['cpv'] = build_cpv
				attDict['useflags'] = final_use_list
				attDict['iuse'] = iuse_flags_list2
				config_cpv_listDict[config_id] = attDict

			# Clean some cache
			myportdb_setup.close_caches()
			portage.portdbapi.portdbapi_instances.remove(myportdb_setup)
		return config_cpv_listDict

	def get_ebuild_metadata(self, cpv, repo):
		# Get the auxdbkeys infos for the ebuild
		try:
			ebuild_auxdb_list = self._myportdb.aux_get(cpv, portage.auxdbkeys, myrepo=repo)
		except:
			ebuild_auxdb_list = []
		else:
			for i in range(len(ebuild_auxdb_list)):
				if ebuild_auxdb_list[i] == '':
					ebuild_auxdb_list[i] = ''
			return ebuild_auxdb_list

	def get_packageDict(self, pkgdir, cpv, repo):

		#Get categories, package and version from cpv
		ebuild_version_tree = portage.versions.cpv_getversion(cpv)
		element = portage.versions.cpv_getkey(cpv).split('/')
		categories = element[0]
		package = element[1]

		# Make a checksum of the ebuild
		try:
			ebuild_version_checksum_tree = portage.checksum.sha256hash(pkgdir + "/" + package + "-" + ebuild_version_tree + ".ebuild")[0]
		except:
			ebuild_version_checksum_tree = "0"
			log_msg = "QA: Can't checksum the ebuild file. %s on repo %s" % (cpv, repo,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			log_msg = "C %s:%s ... Fail." % (cpv, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			ebuild_version_cvs_revision_tree = '0'
		else:
			ebuild_version_cvs_revision_tree = get_ebuild_cvs_revision(pkgdir + "/" + package + "-" + ebuild_version_tree + ".ebuild")

		# Get the ebuild metadata
		ebuild_version_metadata_tree = self.get_ebuild_metadata(cpv, repo)
		# if there some error to get the metadata we add rubish to the
		# ebuild_version_metadata_tree and set ebuild_version_checksum_tree to 0
		# so it can be updated next time we update the db
		if ebuild_version_metadata_tree  == []:
			log_msg = " QA: %s have broken metadata on repo %s" % (cpv, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			ebuild_version_metadata_tree = ['','','','','','','','','','','','','','','','','','','','','','','','','']
			ebuild_version_checksum_tree = '0'

		# add the ebuild info to the dict packages
		attDict = {}
		attDict['repo'] = repo
		attDict['ebuild_version_tree'] = ebuild_version_tree
		attDict['ebuild_version_checksum_tree']= ebuild_version_checksum_tree
		attDict['ebuild_version_metadata_tree'] = ebuild_version_metadata_tree
		#attDict['ebuild_version_text_tree'] = ebuild_version_text_tree[0]
		attDict['ebuild_version_revision_tree'] = ebuild_version_cvs_revision_tree
		return attDict

	def add_new_build_job_db(self, ebuild_id_list, packageDict, config_cpv_listDict):
		# Get the needed info from packageDict and config_cpv_listDict and put that in buildqueue
		# Only add it if ebuild_version in packageDict and config_cpv_listDict match
		if config_cpv_listDict is not None:
			# Unpack config_cpv_listDict
			for k, v in config_cpv_listDict.iteritems():
				config_id = k
				build_cpv = v['cpv']
				iuse_flags_list = list(set(v['iuse']))
				use_enable= v['useflags']
				use_disable = list(set(iuse_flags_list).difference(set(use_enable)))
				# Make a dict with enable and disable use flags for ebuildqueuedwithuses
				use_flagsDict = {}
				for x in use_enable:
					use_flagsDict[x] = 'True'
				for x in use_disable:
					use_flagsDict[x] = 'False'
				# Unpack packageDict
				i = 0
				for k, v in packageDict.iteritems():
					ebuild_id = ebuild_id_list[i]

					# Comper and add the cpv to buildqueue
					if build_cpv == k:
						add_new_build_job(self._conn, ebuild_id, config_id, use_flagsDict)

						# B = Build cpv use-flags config
						hostname, config = get_config(self._conn, config_id)

						# FIXME log_msg need a fix to log the use flags corect.
						log_msg = "B %s:%s USE: %s %s:%s" %  (k, v['repo'], use_flagsDict, hostname, config,)
						add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
					i = i +1

	def get_package_metadataDict(self, pkgdir, package_id):
		# Make package_metadataDict
		attDict = {}
		package_metadataDict = {}
		# changelog_checksum_tree = portage.checksum.sha256hash(pkgdir + "/ChangeLog")
		# changelog_text_tree = get_file_text(pkgdir + "/ChangeLog")
		herd = None
		pkg_md = MetaDataXML(pkgdir + "/metadata.xml", herd)
		#metadata_xml_text_tree = get_file_text(pkgdir + "/metadata.xml")
		# attDict['changelog_checksum'] =  changelog_checksum_tree[0]
		# attDict['changelog_text'] =  changelog_text_tree
		tmp_herds = pkg_md.herds()
		if tmp_herds == ():
			attDict['metadata_xml_herds'] = 'none'
		else:
			attDict['metadata_xml_herds'] = tmp_herds[0]
		md_email_list = []
		for maint in pkg_md.maintainers():
			md_email_list.append(maint.email)
		if md_email_list == []:
			if tmp_herds == ():
				log_msg = "Metadata file %s missing Email" % (pkgdir + "/metadata.xml")
				add_zobcs_logs(self._conn, log_msg, "qa", self._config_id)
			md_email_list.append(attDict['metadata_xml_herds'] + '@gentoo.org')
		attDict['metadata_xml_email'] = md_email_list
		attDict['metadata_xml_checksum'] =  portage.checksum.sha256hash(pkgdir + "/metadata.xml")[0]
		#attDict['metadata_xml_text'] =  metadata_xml_text_tree
		package_metadataDict[package_id] = attDict
		return package_metadataDict

	def add_package(self, packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list, manifest_checksum_tree):
		# Use packageDict to update the db
		ebuild_id_list = add_new_ebuild_sql(self._conn, package_id, packageDict)
		
		# Make old ebuilds unactive
		for ebuild_id in ebuild_id_list:
			new_ebuild_id_list.append(ebuild_id)
		for ebuild_id in get_ebuild_id_list(self._conn, package_id):
			if not ebuild_id in new_ebuild_id_list:
				if not ebuild_id in old_ebuild_id_list:
					old_ebuild_id_list.append(ebuild_id)
		if not old_ebuild_id_list == []:
			add_old_ebuild(self._conn, package_id, old_ebuild_id_list)

		package_metadata_checksum_sql = get_package_metadata_sql(self._conn, package_id)
		if package_metadata_checksum_sql is None or package_metadata_checksum_sql != package_metadataDict[package_id]['metadata_xml_checksum']:
			update_package_metadata(self._conn, package_metadataDict)

		# update the cp manifest checksum
		update_manifest_sql(self._conn, package_id, manifest_checksum_tree)

		# Get the best cpv for the configs and add it to config_cpv_listDict
		cp = get_cp_from_package_id(self._conn, package_id)
		configs_id_list  = get_config_id_list(self._conn)
		config_cpv_listDict = self.config_match_ebuild(cp, configs_id_list)

		# Add the ebuild to the build jobs table if needed
		self.add_new_build_job_db(ebuild_id_list, packageDict, config_cpv_listDict)

	def add_new_package_db(self, cp, repo):
		# Add new categories package ebuild to tables package and ebuilds
		# C = Checking
		# N = New Package
		log_msg = "C %s:%s" % (cp, repo)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		log_msg = "N %s:%s" % (cp, repo)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		repodir = self._myportdb.getRepositoryPath(repo)
		pkgdir = repodir + "/" + cp # Get RepoDIR + cp

		# Get the cp manifest file checksum.
		try:
			manifest_checksum_tree = portage.checksum.sha256hash(pkgdir + "/Manifest")[0]
		except:
			manifest_checksum_tree = "0"
			log_msg = "QA: Can't checksum the Manifest file. :%s" % (cp, repo,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			log_msg = "C %s:%s ... Fail." % (cp, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			return
		package_id = add_new_manifest_sql(self._conn, cp, repo)
		
		package_metadataDict = self.get_package_metadataDict(pkgdir, package_id)
		# Get the ebuild list for cp
		mytree = []
		mytree.append(repodir)
		ebuild_list_tree = self._myportdb.cp_list(cp, use_cache=1, mytree=mytree)
		if ebuild_list_tree == []:
			log_msg = "QA: Can't get the ebuilds list. %s:%s" % (cp, repo,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			log_msg = "C %s:%s ... Fail." % (cp, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			return

		# Make the needed packageDict with ebuild infos so we can add it later to the db.
		packageDict ={}
		new_ebuild_id_list = []
		old_ebuild_id_list = []
		for cpv in sorted(ebuild_list_tree):
			packageDict[cpv] = self.get_packageDict(pkgdir, cpv, repo)

		self.add_package(packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list, manifest_checksum_tree)
		log_msg = "C %s:%s ... Done." % (cp, repo)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)

	def update_package_db(self, package_id):
		# Update the categories and package with new info
		# C = Checking
		cp, repo = get_cp_repo_from_package_id(self._conn, package_id)
		log_msg = "C %s:%s" % (cp, repo)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		repodir = self._myportdb.getRepositoryPath(repo)
		pkgdir = repodir + "/" + cp # Get RepoDIR + cp

		# Get the cp mainfest file checksum
		try:
			manifest_checksum_tree = portage.checksum.sha256hash(pkgdir + "/Manifest")[0]
		except:
			manifest_checksum_tree = "0"
			log_msg = "QA: Can't checksum the Manifest file. %s:%s" % (cp, repo,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			log_msg = "C %s:%s ... Fail." % (cp, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			return

		# if we NOT have the same checksum in the db update the package
		if manifest_checksum_tree != get_manifest_db(self._conn, package_id):

			# U = Update
			log_msg = "U %s:%s" % (cp, repo)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)

			# Get the ebuild list for cp
			mytree = []
			mytree.append(repodir)
			ebuild_list_tree = self._myportdb.cp_list(cp, use_cache=1, mytree=mytree)
			if ebuild_list_tree == []:
				log_msg = "QA: Can't get the ebuilds list. %s:%s" % (cp, repo,)
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				log_msg = "C %s:%s ... Fail." % (cp, repo)
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				return
			packageDict ={}
			new_ebuild_id_list = []
			old_ebuild_id_list = []
			for cpv in sorted(ebuild_list_tree):

				# split out ebuild version
				ebuild_version_tree = portage.versions.cpv_getversion(cpv)
				
				# Get packageDict for cpv
				packageDict[cpv] = self.get_packageDict(pkgdir, cpv, repo)

				# Get the checksum of the ebuild in tree and db
				ebuild_version_checksum_tree = packageDict[cpv]['ebuild_version_checksum_tree']
				checksums_db = get_ebuild_checksum(self._conn, package_id, ebuild_version_tree)
				# check if we have dupes of the checksum from db
				if checksums_db is None:
					ebuild_version_manifest_checksum_db = None
				elif len(checksums_db) >= 2:
					# FIXME: Add function to fix the dups.
					for checksum in checksums_db:
						ebuilds_id = get_ebuild_id_db(self._conn, checksum, package_id)
						log_msg = "U %s:%s:%s Dups of checksums" % (cpv, repo, ebuilds_id,)
						add_zobcs_logs(self._conn, log_msg, "error", self._config_id)
						log_msg = "C %s:%s ... Fail." % (cp, repo)
						add_zobcs_logs(self._conn, log_msg, "error", self._config_id)
					return

				else:
					ebuild_version_manifest_checksum_db = checksums_db[0]

				# Check if the checksum have change
				if ebuild_version_manifest_checksum_db is None:
					# N = New ebuild
					log_msg = "N %s:%s" % (cpv, repo,)
					add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				elif  ebuild_version_checksum_tree != ebuild_version_manifest_checksum_db:
					# U = Updated ebuild
					log_msg = "U %s:%s" % (cpv, repo,)
					add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				else:
					# Remove cpv from packageDict and add ebuild to new ebuils list
					del packageDict[cpv]
					new_ebuild_id_list.append(get_ebuild_id_db(self._conn, ebuild_version_checksum_tree, package_id)[0])
			package_metadataDict = self.get_package_metadataDict(pkgdir, package_id)
			self.add_package(packageDict, package_metadataDict, package_id, new_ebuild_id_list, old_ebuild_id_list, manifest_checksum_tree)

		log_msg = "C %s:%s ... Done." % (cp, repo)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)