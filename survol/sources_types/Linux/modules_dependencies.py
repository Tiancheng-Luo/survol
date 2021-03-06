#!/usr/bin/env python

"""
Linux modules dependencies
"""

import lib_common
import lib_util
import sys
import socket
import lib_modules

from lib_properties import pc

#
# The modules.dep as generated by module-init-tools depmod,
# lists the dependencies for every module in the directories
# under /lib/modules/version, where modules.dep is. 
#
# cat /proc/version
# Linux version 2.6.24.7-desktop586-2mnb (qateam@titan.mandriva.com) (gcc version 4.2.3 (4.2.3-6mnb1)) #1 SMP Thu Oct 30 17:39:28 EDT 2008
# ls /lib/modules/$(cat /proc/version | cut -d " " -f3)/modules.dep
#
# /lib/modules/2.6.24.7-desktop586-2mnb/modules.dep
# /lib/modules/2.6.24.7-desktop586-2mnb/dkms-binary/drivers/char/hsfmc97via.ko.gz: /lib/modules/2.6.24.7-desktop586-2mnb/dkms-binary/drivers/char/hsfserial.ko.gz /lib/modules/2.6.24.7-desktop586-2mnb/dkms-binary/drivers/char/hsfengine.ko.gz /lib/modules/2.6.24.7-desktop586-2mnb/dkms-binary/drivers/char/hsfosspec.ko.gz /lib/modules/2.6.24.7-desktop586-2mnb/kernel/drivers/usb/core/usbcore.ko.gz /lib/modules/2.6.24.7-desktop586-2mnb/dkms-binary/drivers/char/hsfsoar.ko.gz
#
#




def Main():
	cgiEnv = lib_common.CgiEnv()

	grph = cgiEnv.GetGraph()

	# TODO: The dependency network is huge, so we put a limit, for the moment.
	maxCnt=0

	try:
		modudeps = lib_modules.Dependencies()
	except:
		errorMsg = sys.exc_info()[1]
		lib_common.ErrorMessageHtml("Caught:"+str(errorMsg))

	for module_name in modudeps:

		# NOT TOO MUCH NODES: BEYOND THIS, IT IS FAR TOO SLOW, UNUSABLE.
		# HARDCODE_LIMIT
		maxCnt += 1
		if maxCnt > 2000:
			break

		file_parent = lib_modules.ModuleToNode(module_name)
		file_child = None
		for module_dep in modudeps[ module_name ]:

			# print ( module_name + " => " + module_dep )

			# This generates a directed acyclic graph,
			# but not a tree in the general case.
			file_child = lib_modules.ModuleToNode(module_dep)

			grph.add( ( file_parent, pc.property_module_dep, file_child ) )
		# TODO: Ugly trick, otherwise nodes without connections are not displayed.
		# TODO: I think this is a BUG in the dot file generation. Or in RDF ?...
		if file_child is None:
			grph.add( ( file_parent, pc.property_information, lib_common.NodeLiteral("") ) )

	# Splines are rather slow.
	if maxCnt > 100:
		layoutType = "LAYOUT_XXX"
	else:
		layoutType = "LAYOUT_SPLINE"
	cgiEnv.OutCgiRdf( layoutType)

if __name__ == '__main__':
	Main()
