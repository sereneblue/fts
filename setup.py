from setuptools import setup, find_packages
from fts import __version__
import os

setup(
	name ='fts',
    version = __version__,
    description = 'Instantly find subtitles via the command line',
    url = 'https://github.com/sereneblue/fts',
    author = 'sereneblue',
    license = "GPLv3",
    packages = find_packages(exclude=['docs', 'tests*']),
    classifiers = [
		'Intended Audience :: Developers',
		'Environment :: Console',
		'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
    ],
    keywords = ['subtitles', 'opensubtitles', 'subscene', 'cli'],
    install_requires = ['requests', 'docopt'],
    entry_points = {
    	'console_scripts':[
    		'fts=fts.__main__:main'
    	],
    }
)
