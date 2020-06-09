#!/usr/bin/python2
from distutils.core import setup

setup(name='BOSS modules',
      version='0.7.0',
      description='Helper modules for BOSS participants',
      author='Islam Amer',
      author_email='islam.amer@jollamobile.com',
      url='https://github.com/MeeGoIntegration/boss-standard-workflow.git',
      packages=['ots', 'boss', 'boss.bz'],
      package_dir={'ots': 'ots',
                   'boss': 'boss',
                   'boss.bz': 'boss/bz'},
      py_modules=['repo_diff']
)
