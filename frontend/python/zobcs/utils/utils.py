from zobcs.models import EbuildsMetadata
def Get_CPVR(ebuild_id):
	EM = EbuildsMetadata.objects.get(EbuildId = ebuild_id)
	adict = {}
	adict['C'] = EM.EbuildId.PackageId.CategoryId.Category
	adict['P'] = EM.EbuildId.PackageId.Package
	adict['V'] = EM.EbuildId.Version
	adict['R'] = EM.EbuildId.PackageId.RepoId.Repo
	adict['RV'] = EM.Revision
	adict['Id'] = ebuild_id
	return adict
