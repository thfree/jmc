##
## setup.py
## Login : <dax@happycoders.org>
## Started on  Tue Apr 17 21:12:33 2007 David Rousselie
## $Id$
## 
## Copyright (C) 2007 David Rousselie
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##

from setuptools import setup

setup(name = 'jmc', \
      version = '0.3', \
      description = 'Jabber Mail Component', \
      author = 'David Rousselie', \
      author_email = 'dax@happycoders.org', \
      url = 'http://people.happycoders.org/dax/projects/jmc', \
      package_dir = {'': 'src'}, \
      packages = ['jmc', 'jmc.jabber', 'jmc.model'], \
      scripts = ['src/jmc.py'], \
      test_suite = 'jmc.tests.suite')