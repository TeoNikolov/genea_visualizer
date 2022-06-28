### QUICK README
#
# - all filepaths must delimit directories using '/' and NOT '\\'
# - it is assumed that the two skeletons have
#   the same naming convention for joints and the same number of joints
# - it is assumed that the TWH skeleton has 'BVH:' namespace
#   and the GENEA has no namespace

from pyfbsdk import *
from pyfbsdk_additions import *
import os
import xml.etree.ElementTree as etree
import random
    
class SCENE_TYPE_ENUM:
    UNPROCESSED = 0 # work with original files
    PROCESSED = 1 # work with files that have been fully processed

class TARGET_FPS_ENUM:
    FPS30 = 0
    FPS90 = 1

# general settings
RNG_SEED = 42
DO_RENDER = True
SCENE_TYPE = SCENE_TYPE_ENUM.UNPROCESSED

# input/output settings
PROCESS_ALL_TAKES = True
TARGET_FPS = TARGET_FPS_ENUM.FPS30
BVH_MATCH_TOKEN='_30fps.bvh' if SCENE_TYPE == SCENE_TYPE_ENUM.UNPROCESSED else '_30fps-exported.bvh' # for particular take, set the whole take name
WORK_DIR = 'C:/Users/tniko/Documents/Work/GENEA/TWH_DATASET'
OUTPUT_DIR = ''
DIR_CHARACTERIZATION_FILES = 'C:/Users/tniko/AppData/Roaming/Autodesk/HIKCharacterizationTool6/template/'
FILE_CHARACTERIZAION_FILE = 'TalkingWithHands_Roll.xml'
FILE_FBX_MODEL_ORIGINAL = 'C:/Users/tniko/Documents/Work/GENEA/Model/GenevaModel_v2_Tpose_texture-fix.fbx'
FILE_FBX_MODEL = 'C:/Users/tniko/Documents/Work/GENEA/Model/GenevaModel_v2_Tpose_improved.fbx'

# retargeting settings
TWH_NAMESPACE = 'TWH'
GENEA_NAMESPACE = 'GENEA'
ROOT_BONE_NAME = 'b_root'
REFERENCE_BONE_NAME = 'body_world'

# render settings
START_FRAME = 0 # ignored if "RANDOM_START" is set to True
RENDER_DURATION = 900 # consider the FPS of the source (TWH is 90fps) ; 5400 = 1 minute
RANDOM_START = True

def init():
    # create empty scene
    FBApplication().FileNew()

def setup_take(target_fps : TARGET_FPS_ENUM):
    # ensure transport is not playing
    FBPlayerControl().Stop()
    FBPlayerControl().GotoStart()
    if target_fps == TARGET_FPS_ENUM.FPS90:
        FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeModeCustom, 90.0)
    elif target_fps == TARGET_FPS_ENUM.FPS30:
        FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
    return FBSystem().CurrentTake

def create_camera(namespace, name, cameraParentName, cameraOffset, lookAtParentName, lookAtOffset, camFOV=45.0, camRoll=0.0, upVectorName=None, label=''):
    camera = FBFindModelByLabelName(namespace + ":" + name)
    if camera is not None: FBDeleteObjectsByName(name, namespace)
    lookAt = FBModelNull(name + '_lookAt')
    lookAt.ProcessObjectNamespace(FBNamespaceAction.kFBConcatNamespace, namespace)
    lookAt.show = False
    if lookAtParentName != '':
        lookAt.Parent = FBFindModelByLabelName(namespace + ":" + lookAtParentName)
    lookAt.SetVector(lookAtOffset, FBModelTransformationType.kModelTranslation, False)
    lookAt.PropertyList.Find('DrawLink').Data = False
    
    camera = FBCamera(name)
    camera.ProcessObjectNamespace(FBNamespaceAction.kFBConcatNamespace, namespace)
    camera.Interest = lookAt
    camera.Show = False
    camera.FieldOfView = camFOV
    camera.FarPlaneDistance = 10000
    if cameraParentName != '':
        camera.Parent = FBFindModelByLabelName(namespace + ":" + cameraParentName)
    if upVectorName is not None:
        upVectorObj = FBFindModelByLabelName(namespace + ":" + upVectorName)
        camera.UpVector = upVectorObj
    camera.SetVector(cameraOffset, FBModelTransformationType.kModelTranslation, False)
    camera.Roll = camRoll
    camera.ViewShowTimeCode = True
    camera.ResolutionMode = FBCameraResolutionMode.kFBResolutionCustom
    camera.ResolutionWidth = 1280
    camera.ResolutionHeight = 720

def import_FBX(filepath, namespace):
    # merge settings
    model_options = FBFbxOptions(True)
    model_options.NamespaceList = namespace
    model_options.Characters = FBElementAction.kFBElementActionDiscard
    # merge model
    FBApplication().FileMerge(filepath, False, model_options)
    # cleanup namespaces
    objList = FBComponentList()
    FBFindObjectsByName(namespace + ":BVH:*", objList, True, False)
    for o in objList:
        o.ProcessObjectNamespace(FBNamespaceAction.kFBReplaceNamespace, namespace + ":BVH", namespace)
    
def import_BVH(filepath, take_name, namespace):
    # import BVH to current take
    FBApplication().FileImport(filepath, False, True)
    # rename take for consistency
    FBSystem().CurrentTake.Name = take_name.split('.bvh')[0]
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

def t_pose_TWH(twh_namespace, genea_namespace, reference_bone_name, scene_type : SCENE_TYPE_ENUM):
    if scene_type == SCENE_TYPE_ENUM.UNPROCESSED:
        twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
        genea_ref_bone = FBFindModelByLabelName(genea_namespace + ':' + reference_bone_name)
        twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
        genea_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
        twh_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
        genea_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
        for skeleton in FBSystem().Scene.ModelSkeletons:
            if genea_namespace + ':' in skeleton.LongName:
                twh_bone = FBFindModelByLabelName(twh_namespace + ':' + skeleton.Name)
                rotation = FBVector3d(skeleton.Rotation[0], skeleton.Rotation[1], skeleton.Rotation[2])
                twh_bone.SetVector(FBVector3d(rotation), FBModelTransformationType.kModelRotation, False)
    elif scene_type == SCENE_TYPE_ENUM.PROCESSED:
        # processed takes should have t-poses set correctly be default
        for skeleton in FBSystem().Scene.ModelSkeletons:
            skeleton.SetVector(FBVector3d(0,0,0), FBModelTransformationType.kModelRotation, False)
        twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
        twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
        twh_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    else:
        raise ValueError('Error: Unknown SCENE_TYPE_ENUM.')
    FBSystem().Scene.Evaluate()

def retarget(twh_namespace, genea_namespace, reference_bone_name, characterization_filename) -> None:
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
    genea_character = characterize('GENEA', genea_namespace, characterization_filename)
    FBApplication().CurrentCharacter = genea_character
    genea_character.InputCharacter = twh_character
    genea_character.InputType = FBCharacterInputType.kFBCharacterInputCharacter
    genea_character.Active = True
    # finally, restore the TWH reference node rotation to 0
    twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
    twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelRotation, False)
    
def render(output_directory, output_filename, take_fps, start=0, end=0):
    FBPlayerControl().GotoEnd()
    FBPlayerControl().GotoStart()
    # activate camera
    render_camera = FBFindModelByLabelName('Render Camera')
    FBSystem().Scene.Renderer.SetCameraInPane(render_camera , 0)
    # setup camera view
    FBSetCharacterFloorContactsVisibility(False)
    
    if end < start: raise ValueError('End frame cannot be less than start frame!')
    rOptions = FBVideoGrabber().GetOptions()
    rOptions.RenderAudio = False
    rOptions.TimeSpan = FBTimeSpan(FBTime(0,0,0,start), FBTime(0,0,0,end))
    if take_fps == TARGET_FPS_ENUM.FPS90:
        rOptions.TimeSteps = FBTime(0,0,0,3)
    if take_fps == TARGET_FPS_ENUM.FPS30:
        rOptions.TimeSteps = FBTime(0,0,0,1)
    rOptions.CameraResolution = FBCameraResolutionMode.kFBResolutionCustom
    rOptions.ViewingMode = FBVideoRenderViewingMode.FBViewingModeModelsOnly
    rOptions.ShowTimeCode = True
    if end != 0:
        rOptions.OutputFileName = output_directory + output_filename + '-rendered_{}-{}.mp4'.format(start, end)
    else:
        rOptions.OutputFileName = output_directory + output_filename + '-rendered.mp4'
    vManager = FBVideoCodecManager()
    vManager.VideoCodecMode = FBVideoCodecMode.FBVideoCodecStored
    FBApplication().FileRender(rOptions)

for root, subdirs, files in os.walk(WORK_DIR):
    for f in files:
        if BVH_MATCH_TOKEN in f:
            ROOT_DIR = root.replace('\\', '/') + "/"
            TAKE_NAME = f.split('.bvh')[0]
            # setup scene
            init()
            import_BVH(ROOT_DIR + TAKE_NAME + '.bvh', TAKE_NAME, TWH_NAMESPACE)
            import_FBX(FILE_FBX_MODEL_ORIGINAL if SCENE_TYPE == SCENE_TYPE_ENUM.UNPROCESSED else FILE_FBX_MODEL, GENEA_NAMESPACE)
            take = setup_take(TARGET_FPS)
            
            if 'deep' in TAKE_NAME:
                create_camera('', 'Render Camera', '', FBVector3d(211, 165, -111), '', FBVector3d(-2, 100, 1.25))
            else:
                create_camera('', 'Render Camera', '', FBVector3d(-169.83, 200.55, 136.79), '', FBVector3d(26.44, 109.00, 37.70))
                directional_light = FBLight('directional_light')
                directional_light.LightType = FBLightType.kFBLightTypeInfinite
                directional_light.Intensity = 90.0
                directional_light.Show = True
                directional_light.SetVector(FBVector3d(10,10,45), FBModelTransformationType.kModelRotation, False)

            # setup retargeting
            t_pose_TWH(TWH_NAMESPACE, GENEA_NAMESPACE, REFERENCE_BONE_NAME, SCENE_TYPE)
            retarget(TWH_NAMESPACE, GENEA_NAMESPACE, REFERENCE_BONE_NAME, DIR_CHARACTERIZATION_FILES + FILE_CHARACTERIZAION_FILE)
            
            # setup rendering
            if DO_RENDER:
                take_framecount = take.LocalTimeSpan.GetStop().GetFrame()
                if take_framecount < RENDER_DURATION:
                    raise ValueError("The take length is shorter than the render duration.")
                if RANDOM_START:
                    rng = random.Random()
                    rng.seed(take_framecount) # highly unlikely to have 2 identical framerates
                    START_FRAME = rng.randint(0, take_framecount - RENDER_DURATION)    
                    render(OUTPUT_DIR if OUTPUT_DIR != '' else ROOT_DIR, TAKE_NAME, TARGET_FPS, START_FRAME, START_FRAME + RENDER_DURATION)    
                print('Rendered {}'.format(TAKE_NAME))
            
            if not PROCESS_ALL_TAKES:
                break