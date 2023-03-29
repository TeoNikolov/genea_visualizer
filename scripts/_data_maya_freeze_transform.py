import maya.cmds as cmds

# Set to False when trying to run script from within Maya
# Set to True to mimic command line arguments when reading the script as text (i.e. replace the argument placeholders externally using string.replace() )
USE_ARGS=False

# make sure FBX plugin is loaded for handling FBX files
cmds.loadPlugin("fbxmaya.mll")

# import FBX skeleton
cmds.file(force=True, newFile=True)
if USE_ARGS:
    FILE_TPOSED_SKELETON = "MAYA_ARG_FILE_TPOSED_SKELETON"
    FILE_FROZEN_SKELETON = "MAYA_ARG_FILE_FROZEN_SKELETON"
else:
    raise RuntimeError("This script is templated and cannot be executed directly. Its arguments must be set externally.")
#cmds.file(workdir + skeleton_in_filename + ".fbx", i=True, type='FBX', ignoreVersion=True, ra=True, mergeNamespacesOnClash=False, rpr=skeleton_in_filename, importFrameRate=True, importTimeRange="override")
if cmds.file(FILE_TPOSED_SKELETON, q=True, ex=True):
	cmds.file(FILE_TPOSED_SKELETON, i=True, type='FBX', ignoreVersion=True, ra=True, mergeNamespacesOnClash=False, importFrameRate=True, importTimeRange="override")
else:
	raise FileNotFoundError()
	
# freeze bones transforms
cmds.makeIdentity("body_world", apply=True, rotate=True, jointOrient=True)
for bone in cmds.listRelatives('body_world', allDescendents=True):
    cmds.makeIdentity(bone, apply=True, rotate=True, jointOrient=True)

# export the fixed skeleton
cmds.select('body_world', hierarchy=True)
cmds.file(FILE_FROZEN_SKELETON, f=True, op='', type='FBX Export', pr=True, es=True)