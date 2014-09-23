#
# This file is autogenerated during plugin quickstart and overwritten during
# plugin makedist. DO NOT CHANGE IT if you plan to use plugin makedist to update 
# the distribution.
#

from setuptools import setup, find_packages

kwargs = {'author': 'Katherine Dykes',
 'author_email': 'systems.engineering@nrel.gov',
 'description' : 'NREL WISDEM plant finance models',
 'include_package_data': True,
 'install_requires': ['openmdao.main'],
 'keywords': ['openmdao'],
 'license' : 'Apache License, Version 2.0',
 'name': 'Plant_FinanceSE',
 'package_data': {'Plant_FinanceSE': []},
 'package_dir': {'': 'src'},
 'packages': ['plant_financese.nrel_csm_fin', 'plant_financese.basic_finance','test'],
 'zip_safe': False}


setup(**kwargs)

