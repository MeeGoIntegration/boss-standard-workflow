#!/usr/bin/python2
from distutils.core import setup
import os, sys

setup(name = 'ots_participant',
  version = '0.6.0',
  description = 'OTS participant for BOSS',
  author = 'Islam Amer',
  author_email = 'islam.amer@nokia.com',
  url = 'http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-ots',
  packages = ['ots'],
  package_dir = {'ots' : 'ots' }
)
