# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import sys
import os
import portage
from portage import os, _encodings, _unicode_decode
from portage import _unicode_encode
from portage.exception import DigestException, FileNotFound, ParseError, PermissionDenied
from _emerge.Package import Package
from _emerge.RootConfig import RootConfig
from repoman.checks import run_checks
import codecs

class zobcs_repoman(object):
	
	def __init__(self, mysettings, myportdb):
		self._mysettings = mysettings
		self._myportdb = myportdb

	def check_repoman(self, cpv, repo):
		# We run repoman run_checks on the ebuild
		ebuild_version_tree = portage.versions.cpv_getversion(cpv)
		element = portage.versions.cpv_getkey(cpv).split('/')
		categories = element[0]
		package = element[1]
		pkgdir = self._myportdb.getRepositoryPath(repo) + "/" + categories + "/" + package
		full_path = pkgdir + "/" + package + "-" + ebuild_version_tree + ".ebuild"
		root = '/'
		trees = {
		root : {'porttree' : portage.portagetree(root, settings=self._mysettings)}
		}
		root_config = RootConfig(self._mysettings, trees[root], None)
		allvars = set(x for x in portage.auxdbkeys if not x.startswith("UNUSED_"))
		allvars.update(Package.metadata_keys)
		allvars = sorted(allvars)
		myaux = dict(zip(allvars, self._myportdb.aux_get(cpv, allvars, myrepo=repo)))
		pkg = Package(cpv=cpv, metadata=myaux, root_config=root_config, type_name='ebuild')
		fails = []
		try:
			# All ebuilds should have utf_8 encoding.
			f = codecs.open(_unicode_encode(full_path,
			encoding = _encodings['fs'], errors = 'strict'),
			mode = 'r', encoding = _encodings['repo.content'])
			try:
				for check_name, e in run_checks(f, pkg):
					fails.append(check_name + ": " + e)
			finally:
				f.close()
		except UnicodeDecodeError:
			# A file.UTF8 failure will have already been recorded above.
			pass
		# fails will have a list with repoman errors
		return fails