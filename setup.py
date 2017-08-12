#!/usr/bin/env python

#  Installation.
# L avantage avec un setup est que ca devient accessible de Apache et IIS,
# sans devoir specifier le PATH !!!!
# En revanche faudra surement virer revlib ce qui va amener enormement de fichier dans le meme dir.
# Et meme supprimer peut-etre htlib ce qui est tres embetant.
#
# On veut remplacer:
# http://primhillcomputers.ddns.net/Survol/htbin/entity.py
# http://127.0.0.1:8000/htbin/entity.py
#
# par:
# http://primhillcomputers.ddns.net/survol/entity.py
# http://127.0.0.1:8000/survol/entity.py
#
# Un des problemes est que la presence des scripts dans le directory "htbin"
# est une contrainte (Style cgiscripts) mais on peut probablement la supprimer.
# Ce qui est plus embetant est qu'en supprimant htlib et revlib on se retrouve
# avec plein de fichiers dans le meme dossier ???
#
# Detecter la presence de "/htbin/" n'est pas fiable.
#

from distutils.core import setup

setup(name='survol',
      version='1.0dev',
      description='Understanding legacy applications',
      author='Remi Chateauneu',
      author_email='remi.chateauneu@primhillcomputers.com',
      url='http://www.primhillcomputers.com/survol',
      package_dir = {'survol': 'htbin'},
	  requires=['rdflib','cgi','six'],
	  scripts=['cgiserver.py','wsgiserver.py','webserver.py'],
	  data_files=['*.htm','*.js','*.css','Docs/*.txt'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
		  'Intended Audience :: Education',
		  'Intended Audience :: Information Technology',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
		  'Programming Language :: JavaScript',
          'Topic :: Software Development :: Bug Tracking',
		  'Topic :: Education',
		  'Topic :: Software Development :: Documentation',
		  'Topic :: System :: Systems Administration',
		  'Topic :: Documentation'
          ]
	  )