#!/usr/bin/env python

"""
Oracle types
"""

import sys
import lib_common
from lib_properties import pc
import lib_oracle

from sources_types.oracle import schema as oracle_schema
from sources_types.oracle import type as oracle_type

def Main():
	cgiEnv = lib_oracle.OracleEnv()

	oraSchema = cgiEnv.m_entity_id_dict["Schema"]

	grph = cgiEnv.GetGraph()

	sql_query = "SELECT OBJECT_NAME,STATUS,CREATED FROM ALL_OBJECTS WHERE OBJECT_TYPE = 'TYPE' AND OWNER = '" + oraSchema + "'"
	DEBUG("sql_query=%s", sql_query )

	node_oraschema = oracle_schema.MakeUri( cgiEnv.m_oraDatabase, oraSchema )

	result = lib_oracle.ExecuteQuery( cgiEnv.ConnectStr(), sql_query)

	for row in result:
		typeName = str(row[0])
		nodeType = oracle_type.MakeUri( cgiEnv.m_oraDatabase , oraSchema, typeName )
		grph.add( ( node_oraschema, pc.property_oracle_type, nodeType ) )

		lib_oracle.AddLiteralNotNone(grph,nodeType,"Status",row[1])
		lib_oracle.AddLiteralNotNone(grph,nodeType,"Creation",row[2])

	# It cannot work if there are too many views.
	# cgiEnv.OutCgiRdf("LAYOUT_RECT")
	cgiEnv.OutCgiRdf("LAYOUT_RECT",[pc.property_oracle_type])

if __name__ == '__main__':
	Main()
