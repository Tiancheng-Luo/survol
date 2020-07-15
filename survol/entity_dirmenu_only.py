#!/usr/bin/env python

"""
Scripts hierarchy

It is used by entity.py as a module, but also as a script with the CGI parameter mode=menu,
by the D3 interface, to build contextual right-click menu.
It is also used by the client library lib_client , to return all the scritps accessible from an object.
"""

import os
import re
import sys
import lib_util
import lib_common
from lib_properties import pc

# This returns None if a module of a script is usable, otherwise an errir message which explains
# why this script cannot be used in this context: Wrong platform, unavailable resources etc...
# PROBLEM: When an entire directory is not Usable because the file __init__.py
# has a function Usable which returns False, then it still displays a directory, alone.
# Unusable scripts are not displayed in the menu of the scripts of an entity,
# except if a special flag is given, and in this case these error messages are displayed.
def TestUsability(importedMod,entity_type,entity_ids_arr):
    try:
        isUsable = importedMod.Usable(entity_type,entity_ids_arr)
    except :
        return None

    # sys.stderr.write("Module %s : %d\n" %(importedMod.__name__,isUsable    ))
    if isUsable:
        return None

    errorMsg = importedMod.Usable.__doc__
    if errorMsg:
        errorMsg = errorMsg.strip()
    else:
        errorMsg = importedMod.__name__
        if errorMsg:
            errorMsg += " not usable"
        else:
            errorMsg = "No message"
    return errorMsg

def DirMenuReport(depthCall,strMsg):
    """For debugging purpose only."""
    txtMargin = ( "    " * depthCall )
    DEBUG(txtMargin + strMsg)

# TODO: Only return json data, and this script will only return json, nothing else.
def DirToMenu(callbackGrphAdd,parentNode,entity_type,entity_id,entity_host,flagShowAll):

    def DirectoryUsabilityErrorNode(relative_dir,depthCall):
        # Maybe there is a usability test in the current module.
        # The goal is to control all scripts in the subdirectories, from here.
        try:
            entity_class = ".".join( relative_dir.split("/")[2:] )
            #DirMenuReport( depthCall, "entity_class=%s\n"%(entity_class))

            importedMod = lib_util.GetEntityModule(entity_class)
            if importedMod:
                errorMsg = TestUsability(importedMod,entity_type,entity_ids_arr)
                # if flagShowAll and errorMsg ???
                if errorMsg:
                    DEBUG("IsDirectoryUsable errorMsg(1)=%s",errorMsg)
                    # If set to True, the directory is displayed even if all its scripts
                    # are not usable. Surprisingly, the message is not displayed as a subdirectory, but in a separate square.
                    return lib_common.NodeLiteral(errorMsg)
        except IndexError:
            # If we are at the top-level, no interest for the module.
            pass

        return None



    # This lists the scripts and generate RDF nodes.
    # Returns True if something was added.
    def DirToMenuAux(aParentNode,grandParentNode,curr_dir,relative_dir,depthCall = 1):
        #DirMenuReport( depthCall, "curr_dir=%s relative_dir=%s\n"%(curr_dir,relative_dir))
        # In case there is nothing.
        dirs = None
        for path, dirs, files in os.walk(curr_dir):
            break

        # Maybe this class is not defined in our ontology.
        if dirs == None:
            WARNING("DirToMenuAux(2) No content in %s",curr_dir)
            return False

        # Will still be None if nothing is added.
        rdfNode = None
        sub_path = path[ len(curr_dir) : ]

        relative_dir_sub_path = relative_dir + sub_path

        argDir = relative_dir_sub_path.replace("/",".")[1:]

        # If this is a remote host, all scripts are checked because they might have
        # the flag CanProcessRemote which is defined at the script level, not the directory level.
        if not entity_host:
            errDirNode = DirectoryUsabilityErrorNode(relative_dir,depthCall)
            if errDirNode:
                if flagShowAll:
                    argDirSplit = argDir.split(".")
                    currDirNode = lib_util.DirDocNode(".".join(argDirSplit[:-1]),argDirSplit[-1])
                    if not currDirNode:
                        currDirNode = lib_util.NodeLiteral("Cannot parse relative dir:%s"%argDir)
                    callbackGrphAdd( ( grandParentNode, pc.property_script, currDirNode ),depthCall )
                    callbackGrphAdd( ( currDirNode, lib_common.MakeProp("Error"), errDirNode ),depthCall )
                # The directory is not usable, so leave immediately.
                return False


        containsSomething = False
        for dir in dirs:
            #DirMenuReport( depthCall, "dir=%s\n"%(dir))
            # Might be generated by our Python interpreter.
            if dir == "__pycache__":
                continue

            full_sub_dir = os.path.join(curr_dir, dir)

            currDirNode = lib_util.DirDocNode(argDir,dir)

            if not currDirNode:
                #DirMenuReport( depthCall, "currDirNode NONE: argDir=%s dir=%s\n"%(argDir,dir))
                continue

            sub_relative_dir = relative_dir + "/" + dir

            sub_entity_class = ".".join( sub_relative_dir.split("/")[2:] )
            ontoKeys = lib_util.OntologyClassKeys(sub_entity_class)
            #DirMenuReport( depthCall, "Checked ontology of %s: ontoKeys=%s\n"%(sub_entity_class,str(ontoKeys)))

            # TODO: Beware, if not ontology, returns empty array. Why not returning None ?
            if ontoKeys != []:
                #DirMenuReport( depthCall, "Module %s has an ontology so it is a class. Skipping\n"%(sub_relative_dir))
                # BEWARE: NO MORE DEFAULT ONTOLOGY ["Id"]
                continue

            somethingAdded = DirToMenuAux(currDirNode, aParentNode, full_sub_dir,sub_relative_dir,depthCall + 1)
            # This adds the directory name only if it contains a script.
            if somethingAdded:
                # It works both ways, possibly with different properties.
                callbackGrphAdd( ( aParentNode, pc.property_script, currDirNode ), depthCall )
            containsSomething = containsSomething | somethingAdded

        for fil in files:
            # We want to list only the usable Python scripts.
            if not fil.endswith(".py") or fil == "__init__.py":
                continue

            script_path = relative_dir_sub_path + "/" + fil

            #DirMenuReport( depthCall, "DirToMenu encodedEntityId=%s\n" % encodedEntityId)

            url_rdf = genObj.MakeTheNodeFromScript( script_path, entity_type, encodedEntityId )

            errorMsg = None

            try:
                importedMod = lib_util.GetScriptModule(argDir, fil)
            except Exception:
                errorMsg = sys.exc_info()[1]
                #DirMenuReport( depthCall, "DirToMenuAux Cannot import=%s. Caught: %s\n" % (script_path, errorMsg ) )
                importedMod = None
                if not flagShowAll:
                    continue

            if not errorMsg:
                # Show only scripts which want to be shown. Each script can have an optional function
                # called Usable(): If it is there and returns False, the script is not displayed.
                errorMsg = TestUsability(importedMod,entity_type,entity_ids_arr)
                if errorMsg:
                    pass
                    #DEBUG("DirToMenuAux errorMsg(2)=%s",errorMsg)

            # If this is a local host
            if not flagShowAll and errorMsg and not entity_host:
                continue

            # If the entity is on another host, does the script run on remote entities ?
            # The concept of "CanProcessRemote" is a short-hand to avoid checking
            # if the remote is in the entity ids. This flag means:
            # "It is worth anyway investigating on a remote host, if the entity exists there."
            if entity_host:
                try:
                    # Script can be used on a remote entity.
                    can_process_remote = importedMod.CanProcessRemote
                except AttributeError:
                    can_process_remote = False

                # can_process_remote = True
                DEBUG("entity_dir_menu.py DirToMenuAux entity_host=%s can_process_remote=%d",entity_host,can_process_remote)

                if not can_process_remote:
                    if not errorMsg:
                        errorMsg = "%s is local" % ( entity_host )
                    # DirMenuReport( depthCall, "Script %s %s cannot work on remote entities: %s at %s\n" % ( argDir, fil, encodedEntityId , entity_host ) )
                    #DirMenuReport( depthCall, "Script %s %s cannot work on remote entities\n" % ( argDir, fil ) )

                    if not flagShowAll:
                        continue
                else:
                    DirMenuReport( depthCall, "Script %s %s CAN work on remote entities\n" % ( argDir, fil ) )

            # Here, we are sure that the script is added.
            # TODO: If no script is added, should not add the directory?
            rdfNode = lib_common.NodeUrl(url_rdf)
            callbackGrphAdd( ( aParentNode, pc.property_script, rdfNode ), depthCall )

            # Default doc text is file name minus the ".py" extension.
            nodModu = lib_util.FromModuleToDoc(importedMod,fil[:-3])

            callbackGrphAdd( ( rdfNode, pc.property_information, nodModu ), depthCall )

            if errorMsg:
                callbackGrphAdd( ( rdfNode, lib_common.MakeProp("Error"), lib_common.NodeLiteral(errorMsg) ), depthCall )

        # This tells if a script was added in this directory or one of the subdirs.
        return ( rdfNode is not None ) | containsSomething

    if entity_host:
        DEBUG("entity_dir_menu.py DirToMenu entity_host=%s",entity_host)
    encodedEntityId=lib_util.EncodeUri(entity_id)
    entity_ids_arr = lib_util.EntityIdToArray( entity_type, entity_id )

    if entity_type:
        # entity_type might contain a slash, for example: "sqlite/table"
        relative_dir = "/sources_types/" + entity_type
    else:
        relative_dir = "/sources_types"

    directory = lib_util.gblTopScripts + relative_dir

    if entity_host:
        genObj = lib_common.RemoteBox(entity_host)
    else:
        genObj = lib_common.gUriGen

    DirToMenuAux(parentNode,None,directory,relative_dir,depthCall = 1)

################################################################################



# Si entity_type != "" mais entity_id == "", ca n'a pas de sens
# d'afficher les scripts du directory survol/sources/<type>
# car on n'a pas d'id. En revanche, on pourrait afficher selectivement
# des scripts dans "top" qui affichent toutes les entites de ce type.
# Ca revient a selectionner certains scripts.
# On peut faire ca grossierement en filtrant sur le nom.
# Mais on voudrait en fait les afficher directement.
# On peut donc avoir des scripts appeles top/<type>.index.xyzw.py .
# Mais on voudrait en avoir plusieurs, eventuellement.




def Main():

    # This can process remote hosts because it does not call any script, just shows them.
    cgiEnv = lib_common.CgiEnv(
                    can_process_remote = True,
                    parameters = { lib_util.paramkeyShowAll : False })
    entity_id = cgiEnv.m_entity_id
    entity_host = cgiEnv.GetHost()
    flagShowAll = int(cgiEnv.get_parameters( lib_util.paramkeyShowAll ))

    ( nameSpace, entity_type, entity_namespace_type ) = cgiEnv.get_namespace_type()

    if lib_util.IsLocalAddress( entity_host ):
        entity_host = ""

    DEBUG("entity: entity_host=%s entity_type=%s entity_id=%s", entity_host, entity_type, entity_id )

    grph = cgiEnv.GetGraph()

    rootNode = lib_util.RootUri()

    if entity_id != "" or entity_type == "":
        entity_ids_arr = lib_util.EntityIdToArray( entity_type, entity_id )

        # TODO: Plutot qu'attacher tous les sous-directory a node parent,
        # ce serait peut-etre mieux d'avoir un seul lien, et d'afficher
        # les enfants dans une table, un record etc...
        # OU: Certaines proprietes arborescentes seraient representees en mettant
        # les objets dans des boites imbriquees: Tables ou records.
        # Ca peut marcher quand la propriete forme PAR CONSTRUCTION
        # un DAG (Direct Acyclic Graph) qui serait alors traite de facon specifique.

        def CallbackGrphAdd( tripl, depthCall ):
            grph.add(tripl)

        DirToMenu(CallbackGrphAdd,rootNode,entity_type,entity_id,entity_host,flagShowAll)

    cgiEnv.OutCgiRdf( "LAYOUT_RECT", [pc.property_directory,pc.property_script])

if __name__ == '__main__':
    Main()

