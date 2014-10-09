from zobcs.models import Configs, BuildJobsUse, BuildJobs
from zobcs.utils.builduseflags import config_get_use
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django import forms

class BugForm(forms.Form):
	ChoicesComponent = (('Application', 'Application'),
		     	('baselayout', 'baselayout'),
		     	('Core system', 'Core system'),
		     	('Development', 'Development'),
		     	('Eclasses and Profiles', 'Eclasses and Profiles'),
		     	('Games', 'Games'),
		     	('GCC Porting', 'GCC Porting'),
		     	('GNOME', 'GNOME'),
		     	('Hardened', 'Hardened'),
		     	('Java', 'Java'),
		     	('KDE', 'KDE'),
		     	('Keywording and Stabilization', 'Keywording and Stabilization'),
		     	('Library', 'Library'),
		     	('New Ebuilds', 'New Ebuilds'),
		     	('Printing', 'Printing'),
		     	('SELinux', 'SELinux'),
		     	('Server', 'Server'),
		     	('Unspecified', 'Unspecified'))

	Product = forms.CharField(max_length=100, label='Product')
	Component = forms.ChoiceField(widget=forms.Select, choices=ChoicesComponent, label='Component')
	Version = forms.CharField(label='Version')
	Summary = forms.CharField(label='Summary')
	Description = forms.CharField(widget=forms.Textarea, label='Description')
	EmergeInfo = forms.CharField(widget=forms.Textarea, label='emerge --info')
	AssigendTo = forms.EmailField(label='Assigned To')
	CCList = forms.EmailField(label='CC List')
	def __unicode__(self):
		return u'Product : %s, Component : %s, Version : %s, Summary : %s, Description : %s, EmergeInfo : %s, AssigendTo : %s, CCList : %s' % (self.Product, self.Component, self.Version, self.Summary, self.Description, self.EmergeInfo, self.AssigendTo, self.CCList)

class ChoiceBuildConfigSetupSelect(ModelForm):
	Config = forms.ChoiceField(choices=[(x.ConfigId, x.Config) for x in Configs.objects.filter(DefaultConfig = 'False')])
	class Meta:
		model = Configs
		fields = ['Config']
		widget = {
			'Config' : forms.Select(attrs={'class' : 'dropbox' }),
		}

class ChoiceUseFlagsForBuild(forms.Form):
	def __init__(self, ebuild_id, config_id, *args, **kwargs):
		super(ChoiceUseFlagsForBuild, self).__init__(*args, **kwargs)
		UseFlagsDict = config_get_use(ebuild_id, config_id)
		for IUse in UseFlagsDict['iuse']:
			if IUse in UseFlagsDict['usemasked']:
				self.AttrsDisable = True
			else:
				self.AttrsDisable = False
			if IUse.startswith("abi_") or IUse.startswith("python_"):
				self.AttrsDisable = True
			if IUse in UseFlagsDict['useflags']:
				self.AttrsChecked = True
			else:
				self.AttrsChecked = False
			if not IUse.startswith("abi_") and not IUse.startswith("python_"):
				self.fields[IUse] = forms.BooleanField(required = False, initial = self.AttrsChecked)
				self.fields[IUse].widget = forms.CheckboxInput(attrs = {'class' : 'checkbox', 'readonly' : self.AttrsDisable})
		self.fields['Now'] = forms.BooleanField(required = False)
		self.fields['RemoveBin'] = forms.BooleanField(required = False, initial = True)

class EditUseFlagsForBuild(forms.Form):
	def __init__(self, buildjob_id, *args, **kwargs):
		super(EditUseFlagsForBuild, self).__init__(*args, **kwargs)
		UseFlags = BuildJobsUse.objects.filter(BuildJobId = buildjob_id)
		BJ = get_object_or_404(BuildJobs, BuildJobId = buildjob_id)
		for UseId in UseFlags:
			if UseId.Status == "True":
				self.AttrsChecked = True
			else:
				self.AttrsChecked = False
			self.fields[UseId.UseId.Flag] = forms.BooleanField(required = False, initial = self.AttrsChecked)
			self.fields[UseId.UseId.Flag].widget = forms.CheckboxInput(attrs = {'class' : 'checkbox'})
		if BJ.Status == "Now":
			self.AttrsNowChecked = True
		else:
			self.AttrsNowChecked = False
		if BJ.RemoveBin:
			self.AttrsRemoveBinChecked = True
		else:
			self.AttrsRemoveBinChecked = False
		self.fields['Now'] = forms.BooleanField(required = False, initial = self.AttrsNowChecked)
		self.fields['Now'].widget = forms.CheckboxInput(attrs = {'class' : 'checkbox'})
		self.fields['RemoveBin'] = forms.BooleanField(required = False, initial = self.AttrsRemoveBinChecked)
		self.fields['RemoveBin'].widget = forms.CheckboxInput(attrs = {'class' : 'checkbox'})
