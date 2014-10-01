## You will need a __init__.py in the gobs/pym/ dir
## This assumes you have zobcs/ dir as top level

import os

try:
	from setuptools import setup
except ImportError:
	raise
	from ez_setup import use_setuptools
	use_setuptools()
	from setuptools import setup

version = os.path.split(os.path.abspath(__file__))[-2].split('-')[-1]

packages = ['zobcs']

package_dir = {'zobcs': 'backend/zobcs/pym'}

setup(
	name="zobcs",
	version=version,
	author='Zorry',
	author_email='zorry@gentoo.org',
	url='https://github.com/zorry/zobsc.git',
	description='Zorry Open Build Cluster System',
	platforms=["any"],
	license="GPL2",
	packages=packages,
	package_dir=package_dir,
)