#!/usr/bin/python2
from distutils.core import setup
import os, sys

setup(name = 'BOSS modules',
  version = '0.6.0',
  description = 'Helper modules for BOSS participants',
  author = 'Islam Amer',
  author_email = 'islam.amer@nokia.com',
  url =
  'http://meego.gitorious.org/meego-infrastructure-tools/boss-standard-workflow',
  packages = ['ots', 'boss'],
  package_dir = {'ots' : 'ots' , 'boss' : 'boss' }
)
