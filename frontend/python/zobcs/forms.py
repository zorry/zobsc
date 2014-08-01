from zobcs.models import Configs, EbuildsIuse
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

class ChoiceConfig(forms.Form):
	Setups = forms.MultipleChoiceField(
		widget = forms.SelectMultiple
		choices = []
	)

class BuildUse(forms.Form):
	Use = forms.MultipleChoiceField(
		widget = forms.CheckboxSelectMultiple
	)
