from __future__ import print_function

from zobcs.sync import git_pull, sync_tree
from zobcs.buildquerydb import add_buildquery_main, del_buildquery_main
from zobcs.updatedb import update_db_main
from zobcs.mysql_querys import get_config_id, add_zobcs_logs, get_jobs, update_jobs

def jobs_main(session, config_id):
	jobs = get_jobs(session, config_id)
	if jobs in None:
		return
	for job in jobs:
		log_msg = "Job: %s Type: %s" % (job.JobId, job.Type,)
		add_zobcs_logs(session, log_msg, "info", config_id)
		if job == "addbuildquery":
			update_job_list(session, "Runing", job)
			log_msg = "Job %s is runing." % (job.JobId,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result =  add_buildquery_main(job.RunConfigId)
			if result is True:
				update_job_list(session, "Done", job)
				log_msg = "Job %s is done.." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job)
				log_msg = "Job %s did fail." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "delbuildquery":
			update_job_list(session, "Runing", job)
			log_msg = "Job %s is runing." % (job.JobId,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result =  del_buildquery_main(config_id)
			if result is True:
				update_job_list(session, "Done", job)
				log_msg = "Job %s is done.." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job)
				log_msg = "Job %s did fail." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "gsync":
			update_job_list(session, "Runing", job)
			log_msg = "Job %s is runing." % (job.JobId,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result =  git_pull(session)
			if result is True:
				update_job_list(session, "Done", job)
				log_msg = "Job %s is done.." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job)
				log_msg = "Job %s did fail." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "esync":
			update_job_list(session, "Runing", job)
			log_msg = "Job %s is runing." % (job.JobId,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result =  sync_tree(session)
			if result is True:
				update_job_list(session, "Done", job)
				log_msg = "Job %s is done.." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job)
				log_msg = "Job %s did fail." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
		elif job == "updatedb":
			update_job_list(session, "Runing", job)
			log_msg = "Job %s is runing." % (job.JobId,)
			add_zobcs_logs(session, log_msg, "info", config_id)
			result = update_db_main(session)
			if result is True:
				update_job_list(session, "Done", job)
				log_msg = "Job %s is done.." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
			else:
				update_job_list(session, "Fail", job)
				log_msg = "Job %s did fail." % (job.JobId,)
				add_zobcs_logs(session, log_msg, "info", config_id)
	return
