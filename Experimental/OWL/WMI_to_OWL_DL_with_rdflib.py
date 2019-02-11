# https://stackoverflow.com/questions/24017320/using-owlclass-prefix-with-rdflib-and-xml-serialization

from __future__ import print_function
from rdflib.namespace import OWL, RDF, RDFS, XSD
from rdflib import Graph, Literal, Namespace, URIRef

import wmi
import win32com
import pywintypes

# Generate from a URL.

def AddClassToOntology(graph,className,baseClassName, text_descr):

    # Create the node to add to the Graph
    MyClassNode = URIRef(LDT[className])
    MyBaseClassNode = URIRef(LDT[baseClassName])

    # Add the OWL data to the graph
    # <OWL:Class rdf:ID="Service">
    # <rdfs:subClassOf rdf:resource="#System"/>
    # </OWL:Class>
    graph.add((MyClassNode, RDF.type, OWL.Class))
    graph.add((MyClassNode, RDFS.subClassOf, MyBaseClassNode))
    graph.add((MyClassNode, RDFS.label, Literal(className)))
    if text_descr:
        graph.add((MyClassNode, RDFS.comment, Literal(text_descr)))

# "ref:CIM_LogicalElement"
# "ref:CIM_CollectionOfMSEs"
# "ref:__EventConsumer"
# "ref:CIM_Setting"
# "ref:CIM_LogicalElement"
# "ref:CIM_ManagedSystemElement"
# "object:__ACE"
# "object:__Namespace"
# "object:__Trustee"
# "object"
# "Object"
map_types_CIM_to_OWL = {
    "boolean": XSD.boolean,
    "Boolean": XSD.boolean,
    "string": XSD.string,
    "String": XSD.string,
    "uint8": XSD.integer,
    "uint16": XSD.integer,
    "sint32": XSD.integer,
    "uint32": XSD.integer,
    "Uint32": XSD.integer,
    "uint64": XSD.long,
    "Uint64": XSD.long,
    "datetime":XSD.dateTime,
    #"1":XSD.date,
    #"2":XSD.float,
    #"3":XSD.double,
    #"4":XSD.decimal,
    #"5":XSD.time,
    #"7":XSD.duration,
}

def PropNameToType(prop_type):
    try:
        owl_type = map_types_CIM_to_OWL[prop_type]
    except:
        print("tp=",prop_type)
        owl_type = XSD.string
    return owl_type

# Taken from lib_wmi.py
def GetWmiClassFlagUseAmendedQualifiersn(connWmi, classNam):
    clsObj = getattr( connWmi, classNam )
    drv = clsObj.derivation()
    try:
        baseClass = drv[0]
    except IndexError:
        baseClass = ""
    try:
        clsList = [ c for c in connWmi.SubclassesOf (baseClass, win32com.client.constants.wbemFlagUseAmendedQualifiers) if classNam == c.Path_.Class ]
        if not clsList:
            return None
        theCls = clsList[0]
        return theCls
    except pywintypes.com_error:
        return None


# owl_type: "xsd::string" etc... TODO: Transform this into XSD.string etc...
def AddPropertyToOntology(graph,propertyName,prop_type):
    # <OWL:DataTypeProperty rdf:ID="Name">
    # <rdfs:domain rdf:resource="OWL:Thing"/>
    # <rdfs:range rdf:resource="xsd:string"/>
    # </OWL:DataTypeProperty>
    MyDatatypePropertyNode = URIRef(LDT[propertyName])
    graph.add((MyDatatypePropertyNode, RDF.type, OWL.DatatypeProperty))
    graph.add((MyDatatypePropertyNode, RDFS.domain, OWL.Thing))
    owl_type = PropNameToType(prop_type)
    graph.add((MyDatatypePropertyNode, RDFS.range, owl_type))

    #graph.add((MyClassNode, RDF.type, MyDatatypePropertyNode))

# Construct the linked data tools namespace
LDT = Namespace("http://www.primhillcomputers.com/survol#")

# Create the graph
graph = Graph()

cnn = wmi.WMI()

cnt = 0

def GetClassDescr(classNam):
    theCls = GetWmiClassFlagUseAmendedQualifiersn(cnn, classNam)
    if theCls:
        try:
            return str(theCls.Qualifiers_("Description"))
            # pywintypes.com_error: (-2147352567, 'Exception occurred.', (0, u'SWbemQualifierSet', u'Not found ', None, 0, -2147217406), None)
        except pywintypes.com_error:
            return ""
    return ""


map_attributes = {}

for class_name in cnn.classes:
    if cnt > 500: break
    cnt += 1

    cls_obj = getattr(cnn, class_name)

    #klassDescr = cls_obj.Qualifiers_("Description")
    drv_list = cls_obj.derivation()
    if drv_list:
        base_class_name = drv_list[0]
        #outfil.write("""
        #<OWL:Class rdf:ID="%s">
        #<rdfs:subClassOf rdf:resource="#%s"/>
        #</OWL:Class>\n""" % (class_name, base_class_name))
        text_descr = GetClassDescr(class_name)
        AddClassToOntology(graph,class_name, base_class_name, text_descr)

    for p in cls_obj.properties:
        prop_obj = cls_obj.wmi_property(p)

        try:
            only_read = prop_obj.qualifiers['read']
        except:
            only_read = False
        if not only_read:
            map_attributes[prop_obj.name] = prop_obj.type

for prop_name in map_attributes:
    prop_type = map_attributes[prop_name]

    AddPropertyToOntology(graph,prop_name,prop_type)
    #outfil.write("""
    #<OWL:DataTypeProperty rdf:ID="%s">
    #<rdfs:domain rdf:resources="OWL:Thing"/>
    #<rdfs:range rdf:resource="%s"/>
    #</OWL:DataTypeProperty>\n""" % (prop_name, owl_type))

# Bind the OWL and LDT name spaces
graph.bind("owl", OWL)
graph.bind("ldt", LDT)

# https://www.w3.org/TR/owl-ref/#ClassDescription
#    Object properties link individuals to individuals.
#    Datatype properties link individuals to data values.

outfil = open(r"C:\Users\rchateau\Developpement\ReverseEngineeringApps\PythonStyle\Experimental\OWL\onto.owl","w")
# print( graph.serialize(format='xml') )
outfil.write( graph.serialize(format='pretty-xml') )
outfil.close()


print("OK")