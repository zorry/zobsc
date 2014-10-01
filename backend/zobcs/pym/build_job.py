# Get the options from the config file set in zobcs.readconf
from __future__ import print_function
import portage
import os
import re
import sys
import signal

from zobcs.manifest import zobcs_manifest
from zobcs.depclean import do_depclean
from zobcs.flags import zobcs_use_flags
from portage import _encodings
from portage import _unicode_decode
from portage.versions import cpv_getkey
from portage.dep import check_required_use
from zobcs.main import emerge_main
from zobcs.build_log import log_fail_queru
from zobcs.actions import load_emerge_config
from zobcs.mysql_querys import add_zobcs_logs, get_cp_repo_from_package_id, get_packages_to_build

class build_job_action(object):

	def __init__(self, conn, config_id):
		self._config_id = config_id
		self._conn = conn

	def make_build_list(self, build_dict, settings, portdb):
		package_id = build_dict['package_id']
		cp, repo = get_cp_repo_from_package_id(self._conn, package_id)
		element = cp.split('/')
		package = element[1]
		cpv = cp + "-" + build_dict['ebuild_version']
		pkgdir = portdb.getRepositoryPath(repo) + "/" + cp
		init_manifest =  zobcs_manifest(settings, pkgdir)
		try:
			ebuild_version_checksum_tree = portage.checksum.sha256hash(pkgdir + "/" + package + "-" + build_dict['ebuild_version'] + ".ebuild")[0]
		except:
			ebuild_version_checksum_tree = None
		if ebuild_version_checksum_tree == build_dict['checksum']:
			init_flags = zobcs_use_flags(settings, portdb, cpv)
			build_use_flags_list = init_flags.comper_useflags(build_dict)
			log_msg = "build_use_flags_list %s" % (build_use_flags_list,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			manifest_error = init_manifest.check_file_in_manifest(portdb, cpv, build_use_flags_list, repo)
			if manifest_error is None:
				build_dict['check_fail'] = False
				build_cpv_dict = {}
				build_cpv_dict[cpv] = build_use_flags_list
				log_msg = "build_cpv_dict: %s" % (build_cpv_dict,)
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				return build_cpv_dict
			else:
				build_dict['type_fail'] = "Manifest error"
				build_dict['check_fail'] = True
				log_msg = "Manifest error: %s:%s" % (cpv, manifest_error)
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		else:
			build_dict['type_fail'] = "Wrong ebuild checksum"
			build_dict['check_fail'] = True
		if build_dict['check_fail'] is True:
				log_fail_queru(self._conn, build_dict, settings)
				return None
		return build_cpv_dict

	def build_procces(self, buildqueru_cpv_dict, build_dict, settings, portdb):
		build_cpv_list = []
		depclean_fail = True
		for k, build_use_flags_list in buildqueru_cpv_dict.iteritems():
			build_cpv_list.append("=" + k)
			if not build_use_flags_list == None:
				build_use_flags = ""
				for flags in build_use_flags_list:
					build_use_flags = build_use_flags + flags + " "
				filetext = '=' + k + ' ' + build_use_flags
				log_msg = "filetext: %s" % filetext
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
				with open("/etc/portage/package.use/99_autounmask", "a") as f:
     					f.write(filetext)
     					f.write('\n')
     					f.close
		log_msg = "build_cpv_list: %s" % (build_cpv_list,)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		
		argscmd = []
		for emerge_option in build_dict['emerge_options']:
			if emerge_option == '--depclean':
				pass
			elif emerge_option == '--nodepclean':
				pass
			elif emerge_option == '--nooneshot':
				pass
			else:
				if not emerge_option in argscmd:
					argscmd.append(emerge_option)
		for build_cpv in build_cpv_list:
			argscmd.append(build_cpv)
		print("Emerge options: %s" % argscmd)
		log_msg = "argscmd: %s" % (argscmd,)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)

		# close the db for the multiprocessing pool will make new ones
		# and we don't need this one for some time.
		self._conn.close()
		
		# Call main_emerge to build the package in build_cpv_list
		print("Build: %s" % build_dict)
		build_fail = emerge_main(argscmd, build_dict)
		# Run depclean
		if  '--depclean' in build_dict['emerge_options'] and not '--nodepclean' in build_dict['emerge_options']:
			depclean_fail = do_depclean()
		try:
			os.remove("/etc/portage/package.use/99_autounmask")
			with open("/etc/portage/package.use/99_autounmask", "a") as f:
				f.close
		except:
			pass

		# reconnect to the db if needed.
		if not self._conn.is_connected() is True:
			self._conn.reconnect(attempts=2, delay=1)

		build_dict2 = {}
		build_dict2 = get_packages_to_build(self._conn, self._config_id)
		if build_dict['build_job_id'] == build_dict2['build_job_id']:
			log_msg = "build_job %s was not removed" % (build_dict['build_job_id'],)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			print("qurery was not removed")
			if build_fail is True:
				build_dict['type_fail'] = "Emerge faild"
				build_dict['check_fail'] = True
				log_msg = "Emerge faild!"
				add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			else:
				build_dict['type_fail'] = "Querey was not removed"
				build_dict['check_fail'] = True
			log_fail_queru(self._conn, build_dict, settings)
		if build_fail is True:
			return True
		return False

	def procces_build_jobs(self):
		build_dict = {}
		build_dict = get_packages_to_build(self._conn, self._config_id)
		settings, trees, mtimedb = load_emerge_config()
		portdb = trees[settings["ROOT"]]["porttree"].dbapi
		if build_dict is None:
			return
		log_msg = "build_dict: %s" % (build_dict,)
		add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
		if not build_dict['ebuild_id'] is None and build_dict['checksum'] is not None:
			buildqueru_cpv_dict = self.make_build_list(build_dict, settings, portdb)
			log_msg = "buildqueru_cpv_dict: %s" % (buildqueru_cpv_dict,)
			add_zobcs_logs(self._conn, log_msg, "info", self._config_id)
			if buildqueru_cpv_dict is None:
				return
			fail_build_procces = self.build_procces(buildqueru_cpv_dict, build_dict, settings, portdb)
			return
		if not build_dict['emerge_options'] is [] and build_dict['ebuild_id'] is None:
			return
		if not build_dict['ebuild_id'] is None and build_dict['emerge_options'] is None:
			pass
			# del_old_queue(self._conn, build_dict['queue_id'])
