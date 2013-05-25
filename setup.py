#!/usr/bin/env python

from distutils.core import setup

setup(name = 'remark',
      version = '1.6.0',
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
        scripts = ['Remark/remark.py',],
        requires = [
          'markdown (==2.0.0)', 
          'pygments (>=1.5)',
          'pil (>=1.1)',
        ],
     )
