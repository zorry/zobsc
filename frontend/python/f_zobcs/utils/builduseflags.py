# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from f_zobcs.models import *
from django.shortcuts import get_object_or_404
from zobcs.flags import zobcs_use_flags
import portage
def config_get_use(ebuild_id, config_id):
	CS = get_object_or_404(Configs, ConfigId = config_id)
	ConfigSetupName = CS.Config
	ConfigSetupHostName = CS.HostName
	# Change config/setup
	# my_new_setup = "/var/cache/gobs/" + gobs_settings_dict['gobs_gitreponame'] + "/" + host_config + "/"
	my_new_setup = "/"
	mysettings_setup = portage.config(config_root = my_new_setup)
	myportdb_setup = portage.portdbapi(mysettings=mysettings_setup)

	# get cpv
	EM = EbuildsMetadata.objects.get(EbuildId = ebuild_id)
	C = EM.EbuildId.PackageId.CategoryId.Category
	P = EM.EbuildId.PackageId.Package
	V = EM.EbuildId.Version
	build_cpv = C + "/" + P + "-" + V
	
	# Get the iuse and use flags for that config/setup and cpv
	init_useflags = zobcs_use_flags(mysettings_setup, myportdb_setup, build_cpv)
	iuse_flags_list, final_use_list = init_useflags.get_flags()
	iuse_flags_list2 = []
	for iuse_line in iuse_flags_list:
		iuse_flags_list2.append( init_useflags.reduce_flag(iuse_line))
	final_use, use_expand_hidden, usemasked, useforced = init_useflags.get_all_cpv_use()

	# Dict the needed info
	attDict = {}
	attDict['useflags'] = final_use_list
	attDict['iuse'] = iuse_flags_list2
	attDict['usemasked'] = usemasked
	attDict['use_expand_hidden'] = use_expand_hidden

	# Clean some cache
	myportdb_setup.close_caches()
	portage.portdbapi.portdbapi_instances.remove(myportdb_setup)
	return attDict
