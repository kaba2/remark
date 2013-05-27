#!/usr/bin/env python

# Description: Distutils packaging for Remark
# Documentation: dependencies.txt

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
from Remark.Version import remarkVersion

setup(name = 'remark',
      version = remarkVersion(),
      description = 'Remark',
      long_description = 'Generates html documentation for software libraries from lightweight markup.',
      keywords = 'lightweight markup software documentation html',
      author = 'Kalle Rutanen',
      author_email = 'kalle_rutanen@hotmail.com',
      url = 'http://kaba.hilvi.org/remark',
      packages = find_packages(),
      include_package_data = True,
      license = 'MIT',
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
        'Topic :: Software Development :: Documentation',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        ],
      scripts = ['remark.py',],
      install_requires = [
        'markdown==2.0.0', 
        'pygments>=1.5',
        'pillow>=2.0',
        ],
      provides = [
        'Remark'
        ],
      zip_safe = False,
     )
