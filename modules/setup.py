#!/usr/bin/python2
from distutils.core import setup

setup(name='BOSS modules',
      version='0.7.0',
      description='Helper modules for BOSS participants',
      author='Jolla IT',
      author_email='it.team@jollamobile.com',
      url='https://github.com/MeeGoIntegration/boss-standard-workflow.git',
      packages=['ots', 'boss', 'boss.bz', 'rpmUtils', 'yum'],
      package_dir={'ots': 'ots',
                   'boss': 'boss',
                   'boss.bz': 'boss/bz',
                   'rpmUtils': 'rpmUtils',
                   'yum': 'yum'},
      py_modules=['repo_diff']
)
