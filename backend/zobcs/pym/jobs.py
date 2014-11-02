from __future__ import print_function

#from zobcs.sync import git_pull, sync_tree
#from zobcs.buildquerydb import add_buildquery_main, del_buildquery_main
from zobcs.updatedb import update_db_main
from zobcs.sqlquerys import get_config_id, add_zobcs_logs, get_jobs_id, get_job, \
	update_job_list

def jobs_main(session, config_id):
	jobs_id = get_jobs_id(session, config_id)
	if jobs_id in None:
		return
	for job_id in jobs_id:
		job, run_config_id = get_job(session, job_id)
		log_msg = "Job: %s Type: %s" % (job_id, job,)
		add_zobcs_logs(session, log_msg, "info", config_id)
		if job == "addbuildquery":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			#result =  add_buildquery_main(run_config_id)
			#if result is True:
			#	update_job_list(session, "Done", job_id)
			#	log_msg = "Job %s is done.." % (job_id,)
			#	add_zobcs_logs(session, log_msg, "info", config_id)
			#else:
			#	update_job_list(session, "Fail", job_id)
			#	log_msg = "Job %s did fail." % (job_id,)
			#	add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "delbuildquery":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			#result =  del_buildquery_main(config_id)
			#if result is True:
			#	update_job_list(session, "Done", job_id)
			#	log_msg = "Job %s is done.." % (job_id,)
			#	add_zobcs_logs(session, log_msg, "info", config_id)
			#else:
			#	update_job_list(session, "Fail", job_id)
			#	log_msg = "Job %s did fail." % (job_id,)
			#	add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "gsync":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			#result =  git_pull(session)
			if result is True:
				update_job_list(session, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "esync":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			#result =  sync_tree(session)
			if result is True:
				update_job_list(session, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "updatedb":
			update_job_list(session, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result = update_db_main(session, config_id)
			if result is True:
				update_job_list(session, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(session, log_msg, "info", config_id)
	return
