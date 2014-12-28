class ZobcsRouter(object):
	def db_for_read(self, model, **hints):
		"Point all operations on zobcs models to 'zobcs'"
		if model._meta.app_label == 'f_zobcs':
			return 'zobcs'
		return 'default'

	def db_for_write(self, model, **hints):
		"Point all operations on zobcs models to 'zobcs'"
		if model._meta.app_label == 'f_zobcs':
			return 'zobcs'
		return 'default'

	def allow_relation(self, obj1, obj2, **hints):
		"Allow any relation if a both models in zobcs app"
		if obj1._meta.app_label == 'f_zobcs' and obj2._meta.app_label == 'f_zobcs':
			return True
		# Allow if neither is zobcs app
		elif 'f_zobcs' not in [obj1._meta.app_label, obj2._meta.app_label]:
			return True
		return False

	def allow_syncdb(self, db, model):
		if db == 'zobcs' or model._meta.app_label == "f_zobcs":
			return False # we're not using syncdb on our legacy database
		else: # but all other models/databases are fine
			return True
