#!/usr/bin/env python

# Description: Distutils packaging for Remark
# Documentation: dependencies.txt

from distutils.core import setup
from Remark.Version import remarkVersion

# On Windows, `pip install pillow` requires
# Visual Studio, and even a specific version
# of Visual Studio. This is an unreasonable
# requirement for the user. Pillow has binary
# distributions readily available; unfortunately
# pip can not install binary distributions.
# But easy_install can. Since I am unable to
# specify os-specific dependencies, I will have
# to leave the dependency to Pillow out. This
# has then to be manually installed by
# 'easy_install pillow'.

setup(name = 'remark',
      version = remarkVersion(),
      description = 'Remark',
      long_description = 'Generates html documentation for software libraries from lightweight markup.',
      keywords = 'lightweight markup software documentation html',
      author = 'Kalle Rutanen',
      author_email = 'kalle_rutanen@hotmail.com',
      url = 'http://kaba.hilvi.org/remark',
      packages = [
        'Remark', 
        'Remark.Macros',
        'Remark.DocumentTypes',
        'Remark.TagParsers',
        ],
      package_data = {
        'Remark' : [
            'remark_files/*.*',
            'remark_files/highslide/*.*',
            'remark_files/highslide/graphics/*.*',
            'remark_files/highslide/graphics/outlines/*.*',
            ], 
      },
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
      requires = [
        'markdown (==2.0.0)', 
        'pygments (>=1.5)',
        ],
      provides = [
        'Remark'
        ],
     )
