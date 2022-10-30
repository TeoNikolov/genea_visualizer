from pyfbsdk import *
from pyfbsdk_additions import *
import os
import xml.etree.ElementTree as etree
import random

# Set to False when trying to run script from within Maya
# Set to True to mimic command line arguments when reading the script as text (i.e. replace the argument placeholders externally using string.replace() )
USE_ARGS=False

if USE_ARGS:
    TAKE_NAME = 'MOBU_ARG_TAKE_NAME'
    FILE_BVH = 'MOBU_ARG_BVH_FILENAME'
    FILE_GENEA_FBX = 'MOBU_ARG_GENEA_FILENAME'
    FILE_TPOSED_SKELETON = 'MAYA_ARG_FILE_TPOSED_SKELETON'
else:
    TAKE_NAME = 'session15_take18_noFingers_deep5_scale_local_30fps'
    FILE_BVH = 'C:/Users/tniko/Documents/Work/GENEA/TWH_DATASET/session15_take18/' + TAKE_NAME + '.bvh'
    FILE_GENEA_FBX = 'C:/Users/tniko/Documents/Work/GENEA/Model/GenevaModel_v2_Tpose_texture-fix.fbx'
    FILE_TPOSED_SKELETON = 'C:/Users/tniko/Documents/Work/GENEA/TWH_DATASET/session15_take18/' + TAKE_NAME + '_TPOSED_SKELETON.fbx'

def import_FBX(file_path, namespace):
    if not os.path.exists(file_path):
        raise FileNotFoundError('The file does not exist: ' + file_path)
    # merge settings
    model_options = FBFbxOptions(True)
    model_options.NamespaceList = namespace
    model_options.Characters = FBElementAction.kFBElementActionDiscard
    # merge model
    FBApplication().FileMerge(file_path, False, model_options)
    # cleanup namespaces
    objList = FBComponentList()
    FBFindObjectsByName(namespace + ":BVH:*", objList, True, False)
    for o in objList:
        o.ProcessObjectNamespace(FBNamespaceAction.kFBReplaceNamespace, namespace + ":BVH", namespace)
    
def import_BVH(file_path, take_name, namespace):
    if not os.path.exists(file_path):
        raise FileNotFoundError('The file does not exist: ' + file_path)
    # import BVH to current take
    FBApplication().FileImport(file_path, False, True)
    # rename take for consistency
    FBSystem().CurrentTake.Name = take_name
    # cleanup namespaces
    objList = FBComponentList()
    FBFindObjectsByName("BVH:*", objList, True, False)
    for o in objList:
        o.ProcessObjectNamespace(FBNamespaceAction.kFBReplaceNamespace, "BVH", namespace)
    # remove extra reference node
    extra_ref_node = FBFindModelByLabelName(namespace + ':reference')
    if extra_ref_node:
        if len(extra_ref_node.Children) != 1:
            raise RuntimeError('Talking With Hands reference node has mode than 1 child (assumes only 1 child/reference node)')
        extra_ref_node.Children[0].Parent = None
        extra_ref_node.FBDelete()

def t_pose_TWH(twh_namespace, genea_namespace, reference_bone_name):
    twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
    genea_ref_bone = FBFindModelByLabelName(genea_namespace + ':' + reference_bone_name)
    twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    genea_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    twh_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    genea_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    FBSystem().Scene.Evaluate()
    for skeleton in FBSystem().Scene.ModelSkeletons:
        if genea_namespace + ':' in skeleton.LongName:
            twh_bone = FBFindModelByLabelName(twh_namespace + ':' + skeleton.Name)
            rotation = FBVector3d(skeleton.Rotation[0], skeleton.Rotation[1], skeleton.Rotation[2])
            twh_bone.SetVector(FBVector3d(rotation), FBModelTransformationType.kModelRotation, False)
    FBSystem().Scene.Evaluate()
    
def export_FBX(output_path, namespace):
    objList = FBComponentList()
    FBFindObjectsByName(namespace + ":*", objList, True, False)
    for o in objList:
        o.Selected=True
        o.ProcessObjectNamespace(FBNamespaceAction.kFBRemoveAllNamespace, namespace)
        
    # merge settings
    model_options = FBFbxOptions(True)
    model_options.SaveSelectedModelsOnly = True
    model_options.Bones = FBElementAction.kFBElementActionSave
    model_options.Models = FBElementAction.kFBElementActionSave
    model_options.Poses = FBElementAction.kFBElementActionSave
    
    # save FBX
    FBApplication().FileSave(output_path, model_options)

TWH_NAMESPACE = "TWH"
GENEA_NAMESPACE= "GENEA"
REFERENCE_BONE_NAME = 'body_world'

FBApplication().FileNew()
import_BVH(FILE_BVH, TAKE_NAME, TWH_NAMESPACE)
import_FBX(FILE_GENEA_FBX, GENEA_NAMESPACE)
t_pose_TWH(TWH_NAMESPACE, GENEA_NAMESPACE, REFERENCE_BONE_NAME)
export_FBX(FILE_TPOSED_SKELETON, TWH_NAMESPACE)