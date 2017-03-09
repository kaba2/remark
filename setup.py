#!/usr/bin/env python

# Description: Setuptools packaging for Remark
# Documentation: dependencies.txt

from setuptools import setup, find_packages
from Remark.Version import remarkVersion

setup(name = 'remark',
      version = remarkVersion(),
      description = 'Generates html documentation for software libraries from lightweight markup.',
      keywords = 'lightweight markup software documentation html',
      author = 'Kalle Rutanen',
      author_email = 'kaba@hilvi.org',
      url = 'http://kaba.hilvi.org/remark',
      packages = find_packages(),
      include_package_data = True,
      license = 'MIT',
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Topic :: Software Development :: Documentation',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        ],
      scripts = ['remark.py',],
      install_requires = [
        'jsonschema>=2.4',
        'markdown>=2.6', 
        'pillow>=2.0',
        'pygments>=1.5',
        'six>=1.10',
        ],
      zip_safe = False,
     )
