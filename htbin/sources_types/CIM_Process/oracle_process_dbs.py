#!/usr/bin/python

"""
Oracle databases accessed by process
"""

import os
import sys
import psutil
import rdflib

import lib_common
from lib_properties import pc

import lib_oracle

def Main():
	cgiEnv = lib_common.CgiEnv()

	grph = rdflib.Graph()

	try:
		procid = int( cgiEnv.GetId() )
	except Exception:
		lib_common.ErrorMessageHtml("Must provide a pid")


	# For the moment, this is hard-coded.
	# We must list all databases to which the process is connected to.
	# For that, we can:
	# - Try all databases in tnsnames.ora: very slow.
	# - Or snoop packets with Oracle protocol (Hum...)
	# - Or see, among the sockets helpd by the process, which ones are in the tnsnames.ora.


	# THIS IS NOT FINISHED.

	node_process = lib_common.gUriGen.PidUri(procid)

	cgiEnv.OutCgiRdf(grph)

if __name__ == '__main__':
	Main()





