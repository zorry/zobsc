from __future__ import print_function
import re
import os
import platform
import hashlib

from portage.versions import catpkgsplit, cpv_getversion
import portage
from portage.util import writemsg, \
	writemsg_level, writemsg_stdout
from portage import _encodings
from portage import _unicode_encode

from _emerge.main import parse_opts

portage.proxy.lazyimport.lazyimport(globals(),
	'zobcs.actions:action_info',
)

from zobcs.repoman_zobcs import zobcs_repoman
from zobcs.text import get_log_text_list
from zobcs.package import zobcs_package
from zobcs.readconf import get_conf_settings
from zobcs.flags import zobcs_use_flags
from zobcs.ConnectionManager import connectionManager
from zobcs.mysql_querys import add_zobcs_logs, get_config_id, get_ebuild_id_db_checksum, add_new_buildlog, \
	update_manifest_sql, get_package_id, get_build_job_id, get_use_id, get_fail_querue_dict, \
	add_fail_querue_dict, update_fail_times, get_config, get_hilight_info, get_error_info_list, \
	add_old_ebuild

def get_build_dict_db(conn, config_id, settings, pkg):
	myportdb = portage.portdbapi(mysettings=settings)
	cpvr_list = catpkgsplit(pkg.cpv, silent=1)
	categories = cpvr_list[0]
	package = cpvr_list[1]
	repo = pkg.repo
	ebuild_version = cpv_getversion(pkg.cpv)
	log_msg = "Logging %s:%s" % (pkg.cpv, repo,)
	add_zobcs_logs(conn, log_msg, "info", config_id)
	package_id = get_package_id(conn, categories, package, repo)
	build_dict = {}
	build_dict['ebuild_version'] = ebuild_version
	build_dict['package_id'] = package_id
	build_dict['cpv'] = pkg.cpv
	build_dict['categories'] = categories
	build_dict['package'] = package
	build_dict['config_id'] = config_id
	init_useflags = zobcs_use_flags(settings, myportdb, pkg.cpv)
	iuse_flags_list, final_use_list = init_useflags.get_flags_pkg(pkg, settings)
	iuse = []
	for iuse_line in iuse_flags_list:
		iuse.append(init_useflags.reduce_flag(iuse_line))
	iuse_flags_list2 = list(set(iuse))
	use_enable = final_use_list
	use_disable = list(set(iuse_flags_list2).difference(set(use_enable)))
	use_flagsDict = {}
	for x in use_enable:
		use_id = get_use_id(conn, x)
		use_flagsDict[use_id] = 'True'
	for x in use_disable:
		use_id = get_use_id(conn, x)
		use_flagsDict[use_id] = 'False'
	if use_enable == [] and use_disable == []:
		build_dict['build_useflags'] = None
	else:
		build_dict['build_useflags'] = use_flagsDict
	pkgdir = myportdb.getRepositoryPath(repo) + "/" + categories + "/" + package
	ebuild_version_checksum_tree = portage.checksum.sha256hash(pkgdir+ "/" + package + "-" + ebuild_version + ".ebuild")[0]
	build_dict['checksum'] = ebuild_version_checksum_tree
	ebuild_id_list = get_ebuild_id_db_checksum(conn, build_dict)
	if ebuild_id_list is None:
		ebuild_id = None
	elif len(ebuild_id_list) >= 2:
		old_ebuild_id_list = []
		for ebuild_id in ebuild_id_list:
			if ebuild_id != ebuild_id_list[0]:
				log_msg = "%s:%s:%s Dups of checksums" % (pkg.cpv, repo, ebuild_id,)
				add_zobcs_logs(conn, log_msg, "error", config_id)
				old_ebuild_id_list.append(ebuild_id)
		add_old_ebuild(conn, package_id, old_ebuild_id_list)
		ebuild_id = ebuild_id_list[0]
	else:
		ebuild_id = ebuild_id_list[0]
	if ebuild_id is None:
		log_msg = "%s:%s Don't have any ebuild_id!" % (pkg.cpv, repo,)
		add_zobcs_logs(conn, log_msg, "info", config_id)
		update_manifest_sql(conn, package_id, "0")
		init_package = zobcs_package(conn, settings, myportdb)
		init_package.update_package_db(package_id)
		ebuild_id = get_ebuild_id_db_checksum(conn, build_dict)
		if ebuild_id is None:
			log_msg = "%s:%s Don't have any ebuild_id!" % (pkg.cpv, repo,)
			add_zobcs_logs(conn, log_msg, "error", config_id)
			return
	build_dict['ebuild_id'] = ebuild_id
	# FIXME: This fail sometimes with no connection to the db.
	build_job_id = get_build_job_id(conn, build_dict)
	if build_job_id is None:
		build_dict['build_job_id'] = None
	else:
		build_dict['build_job_id'] = build_job_id
	return build_dict

def search_buildlog(conn, logfile_text):
	log_search_list = get_hilight_info(conn)
	index = 0
	hilight_list = []
	for textline in logfile_text:
		index = index + 1
		for search_pattern in log_search_list:
			if re.search(search_pattern['hilight_search'], textline):
				hilight_tmp = {}
				hilight_tmp['startline'] = index - search_pattern['hilight_start']
				hilight_tmp['hilight'] = search_pattern ['hilight_css_id']
				if search_pattern['hilight_search_end'] is None:
					hilight_tmp['endline'] = index + search_pattern['hilight_end']
				else:
					hilight_tmp['endline'] = None
					i = index + 1
					while hilight_tmp['endline'] == None:
						if re.search(search_pattern['hilight_search_end'], logfile_text[i -1]):
							if re.search(search_pattern['hilight_search_end'], logfile_text[i]):
								i = i + 1
							else:
								hilight_tmp['endline'] = i
						else:
							i = i + 1
				hilight_list.append(hilight_tmp)
	new_hilight_dict = {}
	for hilight_tmp in hilight_list:
		add_new_hilight = True
		add_new_hilight_middel = None
		for k, v in sorted(new_hilight_dict.iteritems()):
			if hilight_tmp['startline'] == hilight_tmp['endline']:
				if v['endline'] == hilight_tmp['startline'] or v['startline'] == hilight_tmp['startline']:
					add_new_hilight = False
				if hilight_tmp['startline'] > v['startline'] and hilight_tmp['startline'] < v['endline']:
					add_new_hilight = False
					add_new_hilight_middel = k
			else:
				if v['endline'] == hilight_tmp['startline'] or v['startline'] == hilight_tmp['startline']:
					add_new_hilight = False
				if hilight_tmp['startline'] > v['startline'] and hilight_tmp['startline'] < v['endline']:
					add_new_hilight = False
		if add_new_hilight is True:
			adict = {}
			adict['startline'] = hilight_tmp['startline']
			adict['hilight_css_id'] = hilight_tmp['hilight']
			adict['endline'] = hilight_tmp['endline']
			new_hilight_dict[hilight_tmp['startline']] = adict
		if not add_new_hilight_middel is None:
			adict1 = {}
			adict2 = {}
			adict3 = {}
			adict1['startline'] = new_hilight_dict[add_new_hilight_middel]['startline']
			adict1['endline'] = hilight_tmp['startline'] -1
			adict1['hilight_css_id'] = new_hilight_dict[add_new_hilight_middel]['hilight']
			adict2['startline'] = hilight_tmp['startline']
			adict2['hilight_css_id'] = hilight_tmp['hilight']
			adict2['endline'] = hilight_tmp['endline']
			adict3['startline'] = hilight_tmp['endline'] + 1
			adict3['hilight_css_id'] = new_hilight_dict[add_new_hilight_middel]['hilight']
			adict3['endline'] = new_hilight_dict[add_new_hilight_middel]['endline']
			del new_hilight_dict[add_new_hilight_middel]
			new_hilight_dict[adict1['startline']] = adict1
			new_hilight_dict[adict2['startline']] = adict2
			new_hilight_dict[adict3['startline']] = adict3
	return new_hilight_dict

def get_buildlog_info(conn, settings, pkg, build_dict):
	myportdb = portage.portdbapi(mysettings=settings)
	init_repoman = zobcs_repoman(settings, myportdb)
	logfile_text = get_log_text_list(settings.get("PORTAGE_LOG_FILE"))
	hilight_dict = search_buildlog(conn, logfile_text)
	build_log_dict = {}
	error_log_list = []
	qa_error_list = []
	repoman_error_list = []
	sum_build_log_list = []
	error_info_list = get_error_info_list(conn)
	for k, v in sorted(hilight_dict.iteritems()):
		if v['startline'] == v['endline']:
			error_log_list.append(logfile_text[k -1])
			if v['hilight_css_id'] == "3" or v['hilight_css_id'] == "4": # qa = 3 and 4
				qa_error_list.append(logfile_text[k -1])
		else:
			i = k
			while i != (v['endline'] + 1):
				error_log_list.append(logfile_text[i -1])
				if v['hilight_css_id'] == "3" or v['hilight_css_id'] == "3": # qa = 3 and 4
					qa_error_list.append(logfile_text[i -1])
				i = i +1

	# Run repoman check_repoman()
	repoman_error_list = init_repoman.check_repoman(build_dict['cpv'], pkg.repo)
	if repoman_error_list != []:
		sum_build_log_list.append("1") # repoman = 1
	if qa_error_list != []:
		sum_build_log_list.append("2") # qa = 2
	error_search_line = "^ \\* ERROR: "
	for error_log_line in error_log_list:
		if re.search(error_search_line, error_log_line):
			print(error_log_line)
			for error_info in error_info_list:
				print(error_info)
				if re.search(error_info['error_search'], error_log_line):
					sum_build_log_list.append(error_info['error_id'])

	build_log_dict['repoman_error_list'] = repoman_error_list
	build_log_dict['qa_error_list'] = qa_error_list
	build_log_dict['error_log_list'] = error_log_list
	build_log_dict['summary_error_list'] = sum_build_log_list
	build_log_dict['hilight_dict'] = hilight_dict
	return build_log_dict

def write_msg_file(msg, log_path):
	"""
	Output msg to stdout if not self._background. If log_path
	is not None then append msg to the log (appends with
	compression if the filename extension of log_path
	corresponds to a supported compression type).
	"""
	msg_shown = False
	if log_path is not None:
		try:
			f = open(_unicode_encode(log_path,
			    encoding=_encodings['fs'], errors='strict'),
			mode='ab')
			f_real = f
		except IOError as e:
			if e.errno not in (errno.ENOENT, errno.ESTALE):
				raise
			if not msg_shown:
				writemsg_level(msg, level=level, noiselevel=noiselevel)
		else:
			if log_path.endswith('.gz'):
				# NOTE: The empty filename argument prevents us from
				# triggering a bug in python3 which causes GzipFile
				# to raise AttributeError if fileobj.name is bytes
				# instead of unicode.
				f =  gzip.GzipFile(filename='', mode='ab', fileobj=f)

			f.write(_unicode_encode(msg))
			f.close()
			if f_real is not f:
				f_real.close()

def add_buildlog_main(settings, pkg, trees):
	CM = connectionManager()
	conn = CM.newConnection()
	if not conn.is_connected() is True:
		conn.reconnect(attempts=2, delay=1)
	reader=get_conf_settings()
	zobcs_settings_dict=reader.read_zobcs_settings_all()
	config = zobcs_settings_dict['zobcs_config']
	hostname =zobcs_settings_dict['hostname']
	host_config = hostname + "/" + config
	config_id = get_config_id(conn, config, hostname)
	build_dict = get_build_dict_db(conn, config_id, settings, pkg)
	if build_dict is None:
		log_msg = "Package %s:%s is NOT logged." % (pkg.cpv, pkg.repo,)
		add_zobcs_logs(conn, log_msg, "info", config_id)
		conn.close
		return
	build_log_dict = {}
	build_log_dict = get_buildlog_info(conn, settings, pkg, build_dict)
	error_log_list = build_log_dict['error_log_list']
	build_error = ""
	log_hash = hashlib.sha256()
	build_error = ""
	if error_log_list != []:
		for log_line in error_log_list:
			build_error = build_error + log_line
			log_hash.update(log_line)
	build_log_dict['build_error'] = build_error
	build_log_dict['log_hash'] = log_hash.hexdigest()
	build_log_dict['logfilename'] = settings.get("PORTAGE_LOG_FILE").split(host_config)[1]
	log_msg = "Logfile name: %s" % (settings.get("PORTAGE_LOG_FILE"),)
	add_zobcs_logs(conn, log_msg, "info", config_id)
	log_id = add_new_buildlog(conn, build_dict, build_log_dict)

	if log_id is None:
		log_msg = "Package %s:%s is NOT logged." % (pkg.cpv, pkg.repo,)
		add_zobcs_logs(conn, log_msg, "info", config_id)
	else:
		args = []
		args.append("--info")
		#args.append("=%s" % pkg.cpv)
		myaction, myopts, myfiles = parse_opts(args, silent=True)
		emerge_info_list = action_info(settings, trees, myopts, myfiles)
		for msg in emerge_info_list:
			write_msg_file("%s\n" % msg, emerge_info_logfilename)
		os.chmod(settings.get("PORTAGE_LOG_FILE"), 0o664)
		os.chmod(emerge_info_logfilename, 0o664)
		log_msg = "Package: %s:%s is logged." % (pkg.cpv, pkg.repo,)
		add_zobcs_logs(conn, log_msg, "info", config_id)
		print("\n>>> Logging %s:%s\n" % (pkg.cpv, pkg.repo,))
	conn.close


def log_fail_queru(conn, build_dict, settings):
	config_id = build_dict['config_id']
	fail_querue_dict = get_fail_querue_dict(conn, build_dict)
	if fail_querue_dict is None:
		fail_querue_dict = {}
		fail_querue_dict['build_job_id'] = build_dict['build_job_id']
		fail_querue_dict['fail_type'] = build_dict['type_fail']
		fail_querue_dict['fail_times'] = 1
		add_fail_querue_dict(conn, fail_querue_dict)
	else:
		if fail_querue_dict['fail_times'] < 3:
			fail_querue_dict['fail_times'] = fail_querue_dict['fail_times']+ 1
			fail_querue_dict['build_job_id'] = build_dict['build_job_id']
			fail_querue_dict['fail_type'] = build_dict['type_fail']
			update_fail_times(conn, fail_querue_dict)
			return
		else:
			build_log_dict = {}
			error_log_list = []
			qa_error_list = []
			repoman_error_list = []
			sum_build_log_list = []
			sum_build_log_list.append("2")
			error_log_list.append(build_dict['type_fail'])
			build_log_dict['repoman_error_list'] = repoman_error_list
			build_log_dict['qa_error_list'] = qa_error_list
			build_log_dict['summary_error_list'] = sum_build_log_list
			if build_dict['type_fail'] == 'merge fail':
				error_log_list = []
				for k, v in build_dict['failed_merge'].iteritems():
					error_log_list.append(v['fail_msg'])
			build_log_dict['error_log_list'] = error_log_list
			build_error = ""
			if error_log_list != []:
				for log_line in error_log_list:
					build_error = build_error + log_line
			build_log_dict['build_error'] = build_error
			summary_error = ""
			if sum_build_log_list != []:
				for sum_log_line in sum_build_log_list:
					summary_error = summary_error + " " + sum_log_line
			build_log_dict['log_hash'] = '0'
			useflagsdict = {}
			if build_dict['build_useflags'] == {}:
				for k, v in build_dict['build_useflags'].iteritems():
					use_id = get_use_id(conn, k)
					useflagsdict[use_id] = v
					build_dict['build_useflags'] = useflagsdict
			else:
				build_dict['build_useflags'] = None			
			if settings.get("PORTAGE_LOG_FILE") is not None:
				hostname, config = get_config(conn, config_id)
				host_config = hostname +"/" + config
				build_log_dict['logfilename'] = settings.get("PORTAGE_LOG_FILE").split(host_config)[1]
				os.chmod(settings.get("PORTAGE_LOG_FILE"), 0o664)
			else:
				build_log_dict['logfilename'] = ""
				build_log_dict['hilight_dict'] = {}
			log_id = add_new_buildlog(conn, build_dict, build_log_dict)
