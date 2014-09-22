from zobcs.models import Configs
from zobcs.utils.builduseflags import config_get_use
from django.forms import ModelForm
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
			if IUse.startswith("abi_"):
				self.AttrsDisable = True
			if IUse in UseFlagsDict['useflags']:
				self.AttrsChecked = True
			else:
				self.AttrsChecked = False
			self.fields[IUse] = forms.BooleanField(required = False, initial = self.AttrsChecked)
			self.fields[IUse].widget = forms.CheckboxInput(attrs = {'class' : 'checkbox', 'readonly' : self.AttrsDisable})
		self.fields['Now'] = forms.BooleanField(required = False)
