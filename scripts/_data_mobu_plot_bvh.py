from pyfbsdk import *
from pyfbsdk_additions import *
import os
import xml.etree.ElementTree as etree
import random
import math

# Set to False when trying to run script from within Maya
# Set to True to mimic command line arguments when reading the script as text (i.e. replace the argument placeholders externally using string.replace() )
USE_ARGS=False

CHARACTERIZATION_FILES_DIR = 'C:/Users/tniko/AppData/Roaming/Autodesk/HIKCharacterizationTool6/template/'
CHARACTERIZAION_FILE = 'TalkingWithHands_Roll.xml'
if USE_ARGS:
    TAKE_NAME = "MOBU_ARG_TAKE_NAME"
    FILE_BVH = "MOBU_ARG_BVH_FILENAME"
    FILE_GENEA_FBX = "MOBU_ARG_GENEA_FILENAME"
    FILE_FROZEN_SKELETON = "MAYA_ARG_FILE_FROZEN_SKELETON"
    FILE_BVH_EXPORTED = "MOBU_ARG_BVH_EXPORTED_FILENAME"
    NORMALIZE_ROOT = "MOBU_ARG_NORMALIZE_ROOT"
else:
    TAKE_NAME = 'session14_take5_hasFingers_deep5_scale_local_30fps'
    FILE_BVH = 'C:/Users/tniko/Documents/Work/GENEA/Data/Dev/' + TAKE_NAME + '.bvh'
    FILE_GENEA_FBX = 'C:/Users/tniko/Documents/Work/GENEA/Model/GenevaModel_v2_Tpose_texture-fix.fbx'
    FILE_FROZEN_SKELETON = 'C:/Users/tniko/Documents/Work/GENEA/Data/Dev/' + TAKE_NAME + '_TPOSED_SKELETON-frozen.fbx'
    FILE_BVH_EXPORTED = 'C:/Users/tniko/Documents/Work/GENEA/Data/Dev/' + TAKE_NAME + '-exported.bvh'  
    NORMALIZE_ROOT = False
    
def import_FBX(file_path, namespace):
    if not os.path.exists(file_path):
        raise FileNotFoundError('The file does not exist: ' + file_path)
    # merge settings
    model_options = FBFbxOptions(True)
    model_options.NamespaceList = namespace
    model_options.Characters = FBElementAction.kFBElementActionDiscard
    model_options.TransportSettings = False
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
    if len(extra_ref_node.Children) != 1:
        raise RuntimeError('Talking With Hands reference node has mode than 1 child (assumes only 1 child/reference node)')
    extra_ref_node.Children[0].Parent = None
    extra_ref_node.FBDelete()
    FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)

def t_pose_TWH(twh_namespace, genea_namespace, twh_frozen_namespace, reference_bone_name):
    twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
    twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    twh_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    
    genea_ref_bone = FBFindModelByLabelName(genea_namespace + ':' + reference_bone_name)
    genea_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    genea_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    
    FBSystem().Scene.Evaluate()
    for skeleton in FBSystem().Scene.ModelSkeletons:
        if genea_namespace + ':' in skeleton.LongName:
            twh_bone = FBFindModelByLabelName(twh_namespace + ':' + skeleton.Name)
            rotation = FBVector3d(skeleton.Rotation[0], skeleton.Rotation[1], skeleton.Rotation[2])
            twh_bone.SetVector(FBVector3d(rotation), FBModelTransformationType.kModelRotation, False)
    FBSystem().Scene.Evaluate()
    
def retarget(twh_namespace, twh_frozen_namespace, reference_bone_name, characterization_filename) -> None:
    def characterize(character_name, namespace, characterization_filename):
        character = FBCharacter(character_name)
        character_dict = {}    
        parsed_xml = etree.parse(characterization_filename)
        for line in parsed_xml.iter("item"):
            joint_name = line.attrib.get("value")
            if joint_name:
                joint_name = namespace + ':' + joint_name
                slot_name = line.attrib.get("key")
                mapping_slot = character.PropertyList.Find(slot_name + "Link")
                joint_obj = FBFindModelByLabelName(joint_name)
                if joint_obj:
                    mapping_slot.append(joint_obj)
                
        characterized = character.SetCharacterizeOn(True)
        if not characterized:
            print(character.GetCharacterizeError())
            raise RuntimeError()
        return character
    
    twh_character = characterize('TWH', twh_namespace, characterization_filename)
    twh_frozen_character = characterize('TWH_FROZEN', twh_frozen_namespace, characterization_filename)
    FBApplication().CurrentCharacter = twh_frozen_character 
    twh_frozen_character.InputCharacter = twh_character
    twh_frozen_character.InputType = FBCharacterInputType.kFBCharacterInputCharacter
    twh_frozen_character.Active = True
    # finally, restore the TWH reference node rotation to 0
    twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
    twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelRotation, False)
    # change retargeting settings
    twh_frozen_character.PropertyList.Find('Action Space Compensation Mode', True).Data = 0
    twh_frozen_character.PropertyList.Find('Hips Level Mode', True).Data = 0
    twh_frozen_character.PropertyList.Find('Feet Spacing Mode', True).Data = 0
    twh_frozen_character.PropertyList.Find('Ankle Height Compensation Mode', True).Data = 0
    twh_frozen_character.PropertyList.Find('Mass Center Compensation', True).Data = 0
    # head
    twh_frozen_character.PropertyList.Find('Head Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Head Reach R', True).Data = 0.0
    # spine
    twh_frozen_character.PropertyList.Find('Chest Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Upper Chest Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Lower Chest Reach R', True).Data = 0.0
    # left hand
    twh_frozen_character.PropertyList.Find('Left Elbow Reach', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Hand Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Hand Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Finger Base Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Finger Base Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Arm Stiffness', True).Data = 0.0
    # right hand
    twh_frozen_character.PropertyList.Find('Right Elbow Reach', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Hand Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Hand Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Finger Base Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Finger Base Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Arm Stiffness', True).Data = 0.0
    # left leg
    twh_frozen_character.PropertyList.Find('Left Knee Reach', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Foot Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Foot Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Toe Base Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Toe Base Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Left Leg Stiffness', True).Data = 0.0
    # right leg
    twh_frozen_character.PropertyList.Find('Right Knee Reach', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Foot Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Foot Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Toe Base Reach T', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Toe Base Reach R', True).Data = 0.0
    twh_frozen_character.PropertyList.Find('Right Leg Stiffness', True).Data = 0.0
    
def plot_animation(twh_frozen_namespace):
    # prepare scene
    for take in FBSystem().Scene.Takes:
        if take.Name == TAKE_NAME:
            FBSystem().CurrentTake = take
        else:
            take.FBDelete()
    
    stopFrame = FBSystem().CurrentTake.LocalTimeSpan.GetStop().GetFrame()
    FBSystem().CurrentTake.LocalTimeSpan = FBTimeSpan(FBTime(0,0,0,0), FBTime(0,0,0,stopFrame))
    FBSystem().CurrentTake.ReferenceTimeSpan = FBTimeSpan(FBTime(0,0,0,0), FBTime(0,0,0,stopFrame))
    FBPlayerControl().GotoStart()
    
    # plot animation
    for character in FBSystem().Scene.Characters:
        if twh_frozen_namespace in character.Name:
            FBApplication().CurrentCharacter = character 
    plotOptions = FBPlotOptions()
    plotOptions.PlotOnFrame = True
    plotOptions.PlotAllTakes = False
    plotOptions.PreciseTimeDiscontinuities = False
    plotOptions.PlotTranslationOnRootOnly = True
    plotOptions.PlotLockedProperties = False
    plotOptions.UseConstantKeyReducer = False
    plotOptions.ConstantKeyReducerKeepOneKey = False
    plotOptions.RotationFilterToApply = FBRotationFilter.kFBRotationFilterUnroll
    plotOptions.PlotPeriod = FBTime(0, 0, 0, 1)
    FBApplication().CurrentCharacter.PlotAnimation(FBCharacterPlotWhere.kFBCharacterPlotOnSkeleton, plotOptions)

def normalize_root(twh_frozen_namespace, samples):
    # compute sampling stride
    total_frames = FBSystem().CurrentTake.LocalTimeSpan.GetStop().GetFrame()
    frame_step = total_frames / samples
    
    # sample position and rotation values
    reference_bone = FBFindModelByLabelName(twh_frozen_namespace + ':body_world')
    hip_bone = FBFindModelByLabelName(twh_frozen_namespace + ':b_root')
    pos_acc = [0, 0, 0]
    fwd_acc = [0, 0, 0]
    for i in range(samples):
        frame = int(frame_step * i)
        FBPlayerControl().Goto(FBTime(0,0,0,frame))
        # position
        pos_acc[0] += reference_bone.Translation[0]
        pos_acc[1] += reference_bone.Translation[1]
        pos_acc[2] += reference_bone.Translation[2]
        # rotation
        fwd = FBVector4d()
        rot_mat = FBMatrix()
        hip_bone.GetMatrix(rot_mat, FBModelTransformationType.kModelRotation, True)    
        # rotate Z axis to obtain new forward vector (assumez Z is forward)
        FBVectorMatrixMult(fwd, rot_mat, FBVector4d(0,0,1,0))
        fwd[1] = 0
        fwd_acc[0] += fwd[0]
        fwd_acc[1] = 0
        fwd_acc[2] += fwd[2]
    
    # compute average position and forward vector (normalized)
    pos_acc = [x / samples for x in pos_acc]
    fwd_acc = [x / samples for x in fwd_acc]
    fwd_4d = FBVector4d(fwd_acc[0],fwd_acc[1],fwd_acc[2],0)
    fwd_norm = math.sqrt(FBDot(fwd_4d, fwd_4d))
    fwd_acc[0] = fwd_4d[0] / fwd_norm
    fwd_acc[1] = fwd_4d[1] / fwd_norm
    fwd_acc[2] = fwd_4d[2] / fwd_norm
    # compute angle between the average forward vector and the Z-axis unit vector
    angle = math.acos(FBDot(FBVector4d(0,0,1,0), FBVector4d(fwd_acc[0], fwd_acc[1], fwd_acc[2],0)))
    angle = angle * (180 / math.pi)    
    # if pointing towards X, invert the angle
    if fwd_acc[0] > 0:
        angle = -angle
    
    # interpolate the keys linearly, not cubic as it does automatically
    reference_bone.Translation.GetAnimationNode().DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    hip_bone.Rotation.GetAnimationNode().DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    
    ### process keyframes
    FBPlayerControl().GotoStart()
    i = 0
    while (i <= total_frames):
        ### rotation
        # compute rotation matrix of "angle" degrees around the Y axis
        y_rot_mat = FBMatrix()
        FBRotationToMatrix(y_rot_mat, FBVector3d(0,angle,0), FBRotationOrder.kFBXYZ)
        # multiply rotation around Y axis with the current rotation
        rot_mat = FBMatrix()
        hip_bone.GetMatrix(rot_mat, FBModelTransformationType.kModelRotation, False)
        # set the new rotation
        new_rot = FBVector3d()
        FBMatrixToRotation(new_rot, y_rot_mat * rot_mat)
        hip_bone.SetVector(new_rot, FBModelTransformationType.kModelRotation, False)
        hip_bone.Rotation.Key()
        
        ### position
        original_pos = FBVector3d()
        reference_bone.GetVector(original_pos, FBModelTransformationType.kModelTranslation, False)
        # subtract the average position
        new_pos = FBVector4d(original_pos[0] - pos_acc[0], original_pos[1] - pos_acc[1], original_pos[2] - pos_acc[2],0)
        # rotate the position w.r.t the hip rotation from earlier
        new_pos_rot = FBVector4d()
        FBVectorMatrixMult(new_pos_rot, y_rot_mat, new_pos)
        new_pos_rot = FBVector3d(new_pos_rot[0], new_pos_rot[1], new_pos_rot[2])
        reference_bone.SetVector(new_pos_rot, FBModelTransformationType.kModelTranslation, False)
        reference_bone.Translation.Key()
        
        FBPlayerControl().StepForward()
        i += 1
        
    # optimize curves with linear interpolation and unrolling filter to make values continuous
    unroll_filter = FBFilterManager().CreateFilter('Unroll Rotations')
    unroll_filter.Start = FBTime(0,0,0,0)
    unroll_filter.Stop = FBTime(0,0,0,total_frames)
    unroll_filter.Apply(hip_bone.Rotation.GetAnimationNode(), True)

def export_BVH(output_path, twh_frozen_namespace):
    # center the root so translation is baked to 0,0,0 in BVH spec (does not alter the animation data)
    FBPlayerControl().GotoStart()
    FBFindModelByLabelName(twh_frozen_namespace + ':body_world').SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    objList = FBComponentList()
    FBFindObjectsByName(twh_frozen_namespace + ":*", objList, True, False)
    for o in objList:
        o.Selected=True
        o.ProcessObjectNamespace(FBNamespaceAction.kFBRemoveAllNamespace, twh_frozen_namespace)
    FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
    FBSystem().Scene.Evaluate()
    FBApplication().FileExport(output_path)

GENEA_NAMESPACE= "GENEA"
TWH_NAMESPACE = "TWH"
TWH_FROZEN_NAMESPACE= "TWH_FROZEN"
REFERENCE_BONE_NAME = 'body_world'

FBApplication().FileNew()
# import mocap data
import_BVH(FILE_BVH, TAKE_NAME, TWH_NAMESPACE)
# import GENEA model to align the mocap skeleton
import_FBX(FILE_GENEA_FBX, GENEA_NAMESPACE)
# import the fixed t-pose mocap skeleton
import_FBX(FILE_FROZEN_SKELETON, TWH_FROZEN_NAMESPACE)
t_pose_TWH(TWH_NAMESPACE, GENEA_NAMESPACE, TWH_FROZEN_NAMESPACE, REFERENCE_BONE_NAME)
# delete GENEA model
FBDeleteObjectsByName("", GENEA_NAMESPACE)
# do retargeting
retarget(TWH_NAMESPACE, TWH_FROZEN_NAMESPACE, REFERENCE_BONE_NAME, CHARACTERIZATION_FILES_DIR + CHARACTERIZAION_FILE)
plot_animation(TWH_FROZEN_NAMESPACE)
if NORMALIZE_ROOT:
    normalize_root(TWH_FROZEN_NAMESPACE, 250)
export_BVH(FILE_BVH_EXPORTED, TWH_FROZEN_NAMESPACE)