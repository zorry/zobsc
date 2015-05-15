# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import os
import warnings
from portage import os, _encodings, _unicode_decode
from portage.exception import DigestException, FileNotFound
from portage.localization import _
from portage.manifest import Manifest
import portage

# Copy of portage.digestcheck() but without the writemsg() stuff
def digestcheck(mysettings, pkgdir):
	"""
	Verifies checksums. Assumes all files have been downloaded.
	@rtype: int
	@returns: None on success and error msg on failure
	"""

	myfiles = []
	justmanifest = None
	mysettings['PORTAGE_QUIET'] = '1'

	if mysettings.get("EBUILD_SKIP_MANIFEST") == "1":
		return False
	manifest_path = os.path.join(pkgdir, "Manifest")
	if not os.path.exists(manifest_path):
		return ("!!! Manifest file not found: '%s'") % manifest_path
		mf = Manifest(pkgdir, mysettings["DISTDIR"])
		manifest_empty = True
		for d in mf.fhashdict.values():
			if d:
				manifest_empty = False
				break
		if manifest_empty:
			return ("!!! Manifest is empty: '%s'") % manifest_path
		try:
			if  "PORTAGE_PARALLEL_FETCHONLY" not in self._mysettings:
				mf.checkTypeHashes("EBUILD")
				mf.checkTypeHashes("AUX")
				mf.checkTypeHashes("MISC", ignoreMissingFiles=True)
			for f in myfiles:
				ftype = mf.findFile(f)
				if ftype is None:
					return ("!!! Missing digest for '%s'") % (f,)
				mf.checkFileHashes(ftype, f)
		except FileNotFound as e:
			return ("!!! A file listed in the Manifest could not be found: %s") % str(e)
		except DigestException as e:
			return ("!!! Digest verification failed: %s\nReason: %s\nGot: %s\nExpected: %s") \
				 % (e.value[0], e.value[1], e.value[2], e.value[3])
		# Make sure that all of the ebuilds are actually listed in the Manifest.
		for f in os.listdir(pkgdir):
			pf = None
			if f[-7:] == '.ebuild':
				pf = f[:-7]
			if pf is not None and not mf.hasFile("EBUILD", f):
				return ("!!! A file is not listed in the Manifest: '%s'") \
					% os.path.join(pkgdir, f)
		""" epatch will just grab all the patches out of a directory, so we have to
		make sure there aren't any foreign files that it might grab."""
		filesdir = os.path.join(pkgdir, "files")
		for parent, dirs, files in os.walk(filesdir):
			try:
				parent = _unicode_decode(parent,
					encoding=_encodings['fs'], errors='strict')
			except UnicodeDecodeError:
				parent = _unicode_decode(parent, encoding=_encodings['fs'], errors='replace')
				return ("!!! Path contains invalid character(s) for encoding '%s': '%s'") \
					% (_encodings['fs'], parent)
			for d in dirs:
				d_bytes = d
				try:
					d = _unicode_decode(d, encoding=_encodings['fs'], errors='strict')
				except UnicodeDecodeError:
					d = _unicode_decode(d, encoding=_encodings['fs'], errors='replace')
					return ("!!! Path contains invalid character(s) for encoding '%s': '%s'") \
						% (_encodings['fs'], os.path.join(parent, d))
				if d.startswith(".") or d == "CVS":
					dirs.remove(d_bytes)
				for f in files:
					try:
						f = _unicode_decode(f, encoding=_encodings['fs'], errors='strict')
					except UnicodeDecodeError:
						f = _unicode_decode(f, encoding=_encodings['fs'], errors='replace')
						if f.startswith("."):
							continue
						f = os.path.join(parent, f)[len(filesdir) + 1:]
						return ("!!! File name contains invalid character(s) for encoding '%s': '%s'") \
							% (_encodings['fs'], f)
					if f.startswith("."):
						continue
					f = os.path.join(parent, f)[len(filesdir) + 1:]
					file_type = mf.findFile(f)
					if file_type != "AUX" and not f.startswith("digest-"):
						return ("!!! A file is not listed in the Manifest: '%s'") \
							 % os.path.join(filesdir, f)
	return False

def check_file_in_manifest(pkgdir, mysettings, portdb, cpv, build_use_flags_list, repo):
	myfetchlistdict = portage.FetchlistDict(pkgdir, mysettings, portdb)
	my_manifest = portage.Manifest(pkgdir, mysettings['DISTDIR'], fetchlist_dict=myfetchlistdict, manifest1_compat=False, from_scratch=False)
	ebuild_version = portage.versions.cpv_getversion(cpv)
	package = portage.versions.cpv_getkey(cpv).split("/")[1]
	if my_manifest.findFile(package + "-" + ebuild_version + ".ebuild") is None:
		return "Ebuild file not found."
	tree = portdb.getRepositoryPath(repo)
	cpv_fetchmap = portdb.getFetchMap(cpv, useflags=build_use_flags_list, mytree=tree)
	self._mysettings.unlock()
	try:
		portage.fetch(cpv_fetchmap, mysettings, listonly=0, fetchonly=0, locks_in_subdir='.locks', use_locks=1, try_mirrors=1)
	except:
		self._mysettings.lock()
		return "Can't fetch the file."
	finally:
		self._mysettings.lock()
	try:
		my_manifest.checkCpvHashes(cpv, checkDistfiles=True, onlyDistfiles=False, checkMiscfiles=True)
	except:
		return "Can't fetch the file or the hash failed."
	try:
		portdb.fetch_check(cpv, useflags=build_use_flags_list, mysettings=mysettings, all=False)
	except:	
		return "Fetch check failed."
	return