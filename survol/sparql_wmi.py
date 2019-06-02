# This uses exclusively data from WMI.

#!/usr/bin/python

"""
This SPARQL server translates SPARQL queries into Survol data model.
"""

# For the moment, it just displays the content of the input to standard error,
# so the SparQL protocol can be analysed.

# See Experimental/Test_package_sparqlwrapper.py

import os
import sys
import lib_util
import lib_common
import lib_kbase
import lib_sparql
import lib_wmi

# http://timgolden.me.uk/python/downloads/wmi-0.6b.py



# This is a SPARSL server which executes the query with WMI data.
def Main():
    envSparql = lib_sparql.SparqlEnvironment()

    grph = lib_kbase.MakeGraph()

    sparql_query = envSparql.Query()

    iter_entities_dicts = lib_sparql.QueryEntities(sparql_query, lib_wmi.WmiExecuteQueryCallback)

    sys.stderr.write("iter_entities_dicts=%s\n"%dir(iter_entities_dicts))

    for one_dict_entity in iter_entities_dicts:
        sys.stderr.write("one_dict_entity=%s\n"%one_dict_entity)
        for variable_name, sparql_object in one_dict_entity.items():
            # Dictionary of variable names to PathPredicateObject
            for key,val in sparql_object.m_predicate_object_dict.items():
                grph.add((sparql_object.m_subject_path,key,val))

    # apres execution du sparql dans le nouveau grph
    envSparql.WriteTripleStoreAsString(grph)

if __name__ == '__main__':
    Main()


