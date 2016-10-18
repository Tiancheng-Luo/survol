#!/usr/bin/python

"""
Oracle views
"""

#import re
import sys
#import lib_common
from lib_properties import pc
import lib_oracle
import rdflib

from sources_types.oracle import schema as oracle_schema
from sources_types.oracle import view as oracle_view

def Main():
	cgiEnv = lib_oracle.OracleEnv()

	oraSchema = cgiEnv.m_entity_id_dict["Schema"]

	grph = rdflib.Graph()

	sql_query = "SELECT OBJECT_NAME,STATUS,CREATED FROM DBA_OBJECTS WHERE OBJECT_TYPE = 'VIEW' AND OWNER = '" + oraSchema + "'"
	sys.stderr.write("sql_query=%s\n" % sql_query )

	node_oraschema = oracle_schema.MakeUri( cgiEnv.m_oraDatabase, oraSchema )

	result = lib_oracle.ExecuteQuery( cgiEnv.ConnectStr(), sql_query)

	for row in result:
		viewName = str(row[0])
		nodeView = oracle_view.MakeUri( cgiEnv.m_oraDatabase , oraSchema, viewName )
		grph.add( ( node_oraschema, pc.property_oracle_view, nodeView ) )

		lib_oracle.AddLiteralNotNone(grph,nodeView,"Status",row[1])
		lib_oracle.AddLiteralNotNone(grph,nodeView,"Creation",row[2])

	# It cannot work if there are too many views.
	# cgiEnv.OutCgiRdf(grph,"LAYOUT_RECT")
	cgiEnv.OutCgiRdf(grph,"LAYOUT_RECT",[pc.property_oracle_view])

if __name__ == '__main__':
	Main()
