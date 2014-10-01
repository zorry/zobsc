from __future__ import print_function

from zobcs.sync import git_pull, sync_tree
from zobcs.buildquerydb import add_buildquery_main, del_buildquery_main
from zobcs.updatedb import update_db_main
from zobcs.mysql_querys import get_config_id, add_zobcs_logs, get_jobs_id, get_job, \
	update_job_list, get_job_type

def jobs_main(conn, config_id):
	jobs_id = get_jobs_id(conn, config_id)
	if jobs_id is None:
		return
	for job_id in jobs_id:
		job_type_id, run_config_id = get_job(conn, job_id)
		job = get_job_type(conn, job_type_id)
		log_msg = "Job: %s Type: %s" % (job_id, job,)
		add_zobcs_logs(conn, log_msg, "info", config_id)
		if job == "addbuildquery":
			update_job_list(conn, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(conn, log_msg, "info", config_id)
			result =  add_buildquery_main(run_config_id)
			if result is True:
				update_job_list(conn, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
			else:
				update_job_list(conn, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
		elif job == "delbuildquery":
			update_job_list(conn, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(conn, log_msg, "info", config_id)
			result =  del_buildquery_main(config_id)
			if result is True:
				update_job_list(conn, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
			else:
				update_job_list(conn, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
		elif job == "gsync":
			update_job_list(conn, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(conn, log_msg, "info", config_id)
			result =  git_pull(conn)
			if result is True:
				update_job_list(conn, "Done", job_id)
				log_msg = "Job %s is done.." % (job[1],)
				add_zobcs_logs(conn, log_msg, "info", config_id)
			else:
				update_job_list(conn, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
		elif job == "esync":
			update_job_list(conn, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(conn, log_msg, "info", config_id)
			result =  sync_tree(conn)
			if result is True:
				update_job_list(conn, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
			else:
				update_job_list(conn, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
		elif job == "updatedb":
			update_job_list(conn, "Runing", job_id)
			log_msg = "Job %s is runing." % (job_id,)
			add_zobcs_logs(conn, log_msg, "info", config_id)
			result = update_db_main(conn)
			if result is True:
				update_job_list(conn, "Done", job_id)
				log_msg = "Job %s is done.." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
			else:
				update_job_list(conn, "Fail", job_id)
				log_msg = "Job %s did fail." % (job_id,)
				add_zobcs_logs(conn, log_msg, "info", config_id)
	return
