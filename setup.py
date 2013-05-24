from setuptools import setup

setup(name = 'remark',
      version = '1.6.0',
      description = 'Remark',
      long_description = 'Generates html documentation for software libraries from lightweight markup.',
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
        'Topic :: Software Development :: Documentation',
      ],
      keywords = 'lightweight markup software documentation html',
      url = 'http://kaba.hilvi.org/remark',
      author = 'Kalle Rutanen',
      author_email = 'kalle_rutanen@hotmail.com',
      license = 'MIT',
      packages = ['Remark'],
      install_requires = [
        'markdown == 2.0.0', 
        'pygments >= 1.5',
        'pil >= 1.1',
      ],
      scripts = {
          'Remark/remark.py',
      },
      zip_safe=False)
