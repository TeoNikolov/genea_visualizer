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
import copy
from pathlib import Path
    
class SCENE_TYPE_ENUM:
    UNPROCESSED = 0 # work with original files
    PROCESSED   = 1 # work with files that have been fully processed

class TARGET_FPS_ENUM:
    FPS30 = 0
    FPS90 = 1

class RENDER_MODE:
    STANDARD = FBVideoRenderViewingMode.FBViewingModeStandard
    MODELS   = FBVideoRenderViewingMode.FBViewingModeModelsOnly
    XRAY     = FBVideoRenderViewingMode.FBViewingModeXRay
    CURRENT  = FBVideoRenderViewingMode.FBViewingModeCurrent
    COUNT    = FBVideoRenderViewingMode.FBViewingModeCount

class AUDIO_MODE:
    ENABLED = True
    DISABLED = False
    AUTOMATIC = None # enables audio rendering if an audio file was found for a take

### misc settings
RNG_SEED = 42
FILE_FBX_MODEL_ORIGINAL = 'D:/Files/30-39 Work/2022-05_GENEA_2022/3D/GenevaModel_v2_Tpose_texture-fix.fbx'
FILE_FBX_MODEL = 'D:/Files/30-39 Work/2022-05_GENEA_2022/3D/GenevaModel_v2_Tpose_improved.fbx'

tmpl_scene_settings = {
    "fps"        : TARGET_FPS_ENUM.FPS30,
    "scene_type" : SCENE_TYPE_ENUM.PROCESSED
}

tmpl_io_settings = {
    "input_dir"  : Path('D:/Files/30-39 Work/GENEA_2023/genea_visualizer/scripts/data/retargeted/single/'),
    # where rendered videos are saved, cannot have more than 1 non-existing directory
    "output_dir" : Path('D:/Files/30-39 Work/GENEA_2023/genea_visualizer/scripts/data/retargeted/rendered/'),
    "audio"      : None, # generated automatically
    "bvh_1"      : None, # generated automatically
    "bvh_1_name" : None, # generated automatically
    "bvh_2"      : None, # generated automatically
    "bvh_2_name" : None, # generated automatically
    "fbx"        : None  # generated automatically
}

tmpl_retarget_settings = {
    "twh_ns"                    : 'TWH',
    "genea_ns"                  : 'GENEA',
    "ref_bone"                  : 'body_world',
    "characterization_file"     : 'D:/Files/50-59 Software/52 Settings/Autodesk/MotionBuilder/HIKCharacterizationTool6/template/TalkingWithHands_Roll.xml',
    "preserve_hips_translation" : True
}

tmpl_render_settings = {
    "process_all_takes"    : True,
    "render"               : True,
    "render_audio"         : AUDIO_MODE.AUTOMATIC,
    "mode"                 : RENDER_MODE.MODELS,
    # How long the output video should be, in frames.
    # Set to '0' to render until the end of the take.
    # Consider the FPS of the source (original TWH is 90fps, processed is 30fps).
    # For example, 5400@90 = 1m, 900@30 = 30s
    "duration"             : 900,
    # The frame to start rendering from. Ignored if 'random = True'
    "start_frame"          : 0,
    # Whether to select a start frame at random instead of using the user-specified.
    "random"               : False,
    # If 'random = True', whether the random start should be deterministic
    "random_deterministic" : True
}

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

def import_WAV(filepath):
    audio = FBAudioClip(filepath)

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
    FBSystem().Scene.NamespaceCleanup()

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
    FBSystem().Scene.NamespaceCleanup()
    FBSystem().Scene.Evaluate()

    # add a keyframe to constant anim tracks to prevent accidentally changing them
    objList = FBComponentList()
    FBFindObjectsByName(namespace + ":*", objList, True, False)
    for o in objList:
        if isinstance(o, FBModelSkeleton):
            for n in o.AnimationNode.Nodes:
                n.KeyCandidate()

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
        # commented in order to render the T-posed, pre-normalized data
        #twh_ref_bone.SetVector(FBVector3d(0, -90, 0), FBModelTransformationType.kModelRotation, False)
    else:
        raise ValueError('Error: Unknown SCENE_TYPE_ENUM.')
    FBSystem().Scene.Evaluate()

def retarget(twh_namespace, genea_namespace, reference_bone_name, characterization_filename, preserve_hips_translation) -> None:
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
    genea_character.PropertyList.Find('Character Solver', True).Data = 3
    if preserve_hips_translation:
        genea_character.PropertyList.Find('Hips Level Mode', True).Data = 0
        genea_character.PropertyList.Find('Feet Spacing Mode', True).Data = 0
        genea_character.PropertyList.Find('Ankle Height Compensation Mode', True).Data = 0
        genea_character.PropertyList.Find('Action Space Compensation Mode', True).Data = 0
    # finally, restore the TWH reference node rotation to 0
    twh_ref_bone = FBFindModelByLabelName(twh_namespace + ':' + reference_bone_name)
    twh_ref_bone.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelRotation, False)

def render(render_settings, output_directory, output_filename, take_fps, start=0, end=0):
    FBPlayerControl().GotoEnd()
    FBPlayerControl().GotoStart()
    # activate camera
    render_camera = FBFindModelByLabelName('Render Camera')
    FBSystem().Scene.Renderer.SetCameraInPane(render_camera , 0)
    # setup camera view
    FBSetCharacterFloorContactsVisibility(False)
    
    if end < start: raise ValueError('End frame cannot be less than start frame!')
    rOptions = FBVideoGrabber().GetOptions()
    rOptions.RenderAudio = render_settings["render_audio"]
    rOptions.TimeSpan = FBTimeSpan(FBTime(0,0,0,start), FBTime(0,0,0,end))
    if take_fps == TARGET_FPS_ENUM.FPS90:
        rOptions.TimeSteps = FBTime(0,0,0,3)
    if take_fps == TARGET_FPS_ENUM.FPS30:
        rOptions.TimeSteps = FBTime(0,0,0,1)
    rOptions.CameraResolution = FBCameraResolutionMode.kFBResolutionCustom
    rOptions.ViewingMode = render_settings["mode"]
    rOptions.ShowTimeCode = True
    if end != 0:
        rOptions.OutputFileName = str(output_directory / (output_filename + '-rendered_{}-{}.mp4'.format(start, end)))
    else:
        rOptions.OutputFileName = str(output_directory / (output_filename + '-rendered.mp4'))
    vManager = FBVideoCodecManager()
    vManager.VideoCodecMode = FBVideoCodecMode.FBVideoCodecStored
    FBApplication().FileRender(rOptions)

# Get leaf directories
def get_leaf_dirs(work_dir : Path):
    dirs = []
    for path_object in work_dir.rglob("*"):
        if path_object.is_dir():
            is_leaf = True
            for child_object in path_object.glob("*"):
                if child_object.is_dir():
                    is_leaf = False
            if is_leaf:
                dirs.append(path_object)
    return dirs

# Get a list of files in a folder
def get_files(work_dir : Path):
    files = []
    for path_object in work_dir.rglob("*"):
        if path_object.is_file():
            files.append(path_object)
    return files

def get_take_data(work_dir : Path):
    take_dirs = get_leaf_dirs(work_dir)
    take_names = []
    take_files = []

    for take_dir in take_dirs:
        take_names.append(take_dir.name)
        take_files.append(get_files(take_dir))

    take_data = []
    for i in range(0, len(take_dirs)):
        data = {
            "directory" : take_dirs[i],
            "name" : take_names[i],
            "files" : take_files[i]
        }
        take_data.append(data)
    return take_data

def process_take(take_name, io_settings, scene_settings, retarget_settings, render_settings):
    # setup scene
    dyadic = io_settings["bvh_2"] != None

    init()
    if io_settings["audio"]:
        import_WAV(str(io_settings["audio"]))

    if dyadic:
        import_BVH(str(io_settings["bvh_1"]), io_settings["bvh_1_name"], retarget_settings["twh_ns"] + "_1")
        import_BVH(str(io_settings["bvh_2"]), io_settings["bvh_2_name"], retarget_settings["twh_ns"] + "_2")
        if render_settings["mode"] != RENDER_MODE.XRAY:
            import_FBX(io_settings["fbx"], retarget_settings["genea_ns"] + "_1")
            import_FBX(io_settings["fbx"], retarget_settings["genea_ns"] + "_2")
    else:
        import_BVH(str(io_settings["bvh_1"]), io_settings["bvh_1_name"], retarget_settings["twh_ns"])
        if render_settings["mode"] != RENDER_MODE.XRAY:
            import_FBX(io_settings["fbx"], retarget_settings["genea_ns"])
    take = setup_take(scene_settings["fps"])

    if dyadic:
        create_camera('', 'Render Camera', '', FBVector3d(0, 200, 300), '', FBVector3d(0, 70, 0))
    else:
        if 'deep' in io_settings["bvh_1_name"]:
            create_camera('', 'Render Camera', '', FBVector3d(211, 165, -111), '', FBVector3d(-2, 100, 1.25))
        else:
            create_camera('', 'Render Camera', '', FBVector3d(-169.83, 200.55, 136.79), '', FBVector3d(26.44, 109.00, 37.70))

    light1 = FBLight('directional_light_1')
    light1.LightType = FBLightType.kFBLightTypeInfinite
    light1.Intensity = 80.0
    light1.Show = True
    light1.SetVector(FBVector3d(0,-1000,0), FBModelTransformationType.kModelTranslation, False)
    light1.SetVector(FBVector3d(10,10,45), FBModelTransformationType.kModelRotation, False)

    light2 = FBLight('directional_light_2')
    light2.LightType = FBLightType.kFBLightTypeInfinite
    light2.Intensity = 80.0
    light2.Show = True
    light2.SetVector(FBVector3d(0,-1000,0), FBModelTransformationType.kModelTranslation, False)
    light2.SetVector(FBVector3d(10,10,-45), FBModelTransformationType.kModelRotation, False)

    light3 = FBLight('directional_light_3')
    light3.LightType = FBLightType.kFBLightTypeInfinite
    light3.Intensity = 45.0
    light3.Show = True
    light3.SetVector(FBVector3d(0,-1000,0), FBModelTransformationType.kModelTranslation, False)
    light3.SetVector(FBVector3d(60,0,0), FBModelTransformationType.kModelRotation, False)

    # setup retargeting
    if render_settings["mode"] != RENDER_MODE.XRAY:
        if dyadic:
            t_pose_TWH(retarget_settings["twh_ns"] + "_1", retarget_settings["genea_ns"] + "_1", retarget_settings["ref_bone"], scene_settings["scene_type"])
            retarget(retarget_settings["twh_ns"] + "_1", retarget_settings["genea_ns"] + "_1", retarget_settings["ref_bone"], retarget_settings["characterization_file"], retarget_settings["preserve_hips_translation"])
            t_pose_TWH(retarget_settings["twh_ns"] + "_2", retarget_settings["genea_ns"] + "_2", retarget_settings["ref_bone"], scene_settings["scene_type"])
            retarget(retarget_settings["twh_ns"] + "_2", retarget_settings["genea_ns"] + "_2", retarget_settings["ref_bone"], retarget_settings["characterization_file"], retarget_settings["preserve_hips_translation"])
        else:
            t_pose_TWH(retarget_settings["twh_ns"], retarget_settings["genea_ns"], retarget_settings["ref_bone"], scene_settings["scene_type"])
            retarget(
                retarget_settings["twh_ns"],
                retarget_settings["genea_ns"],
                retarget_settings["ref_bone"],
                retarget_settings["characterization_file"],
                retarget_settings["preserve_hips_translation"])

    # setup rendering
    if render_settings["render"]:
        take_framecount = take.LocalTimeSpan.GetStop().GetFrame()
        if take_framecount < render_settings["duration"]:
            raise ValueError("The take length is shorter than the render duration.")

        # set the start frame
        if render_settings["random"]:
            rng = random.Random()

            if render_settings["random_deterministic"]:
                rng.seed(take_framecount) # highly unlikely to have 2 identical take lengths

            fstart = rng.randint(0, take_framecount - render_settings["duration"] - 1)
        else:
            fstart = render_settings["start_frame"] # this is a global variable

        # set the end frame
        if render_settings["duration"] == 0:
            fend = take_framecount - 1
        elif render_settings["duration"] > 0:
            fend = fstart + render_settings["duration"]
        else:
            raise ValueError("The render duration cannot be less than 0.")

        # render the video
        output_filename = take_name if dyadic else io_settings["bvh_1_name"]
        render(render_settings, io_settings["output_dir"], output_filename, scene_settings["fps"], fstart, fend)
        print('Rendered {}'.format(io_settings["bvh_1_name"]))

take_data = get_take_data(tmpl_io_settings["input_dir"])
take_iters = 0
for take in take_data:
    # copy settings templates
    scene_settings    = copy.deepcopy(tmpl_scene_settings)
    io_settings       = copy.deepcopy(tmpl_io_settings)
    retarget_settings = copy.deepcopy(tmpl_retarget_settings)
    render_settings   = copy.deepcopy(tmpl_render_settings)

    # generate settings
    for f in take["files"]:
        if f.name == take["name"] + ".wav":
            io_settings["audio"] = f

        if f.suffix == ".bvh":
            if io_settings["bvh_1"] == None and "deep" in str(f):
                io_settings["bvh_1"] = f
                io_settings["bvh_1_name"] = f.stem
            elif io_settings["bvh_2"] == None and "shallow" in str(f):
                io_settings["bvh_2"] = f
                io_settings["bvh_2_name"] = f.stem
            else:
                raise RuntimeError("There can be only 2 bvh files in the same folder.")

    # break loop if we want to process only 1 take
    if render_settings["process_all_takes"] == False or render_settings["render"] == False:
        if take_iters == 1:
            break
    take_iters += 1

    # validate settings
    # single BVH must always be at position one
    if io_settings["bvh_1"] == None:
        io_settings["bvh_1"] = io_settings["bvh_2"]
        io_settings["bvh_1_name"] = io_settings["bvh_2_name"]
        io_settings["bvh_2"] = None
        io_settings["bvh_2_name"] = None
        if io_settings["bvh_1"] == None:
            print("Warning: No BVH files present. Skipping...")
            continue

    io_settings["fbx"] = FILE_FBX_MODEL_ORIGINAL if scene_settings["scene_type"] == SCENE_TYPE_ENUM.UNPROCESSED else FILE_FBX_MODEL

    if render_settings["render_audio"] == AUDIO_MODE.AUTOMATIC:
        if io_settings["audio"] != None:
            render_settings["render_audio"] = AUDIO_MODE.ENABLED
        else:
            render_settings["render_audio"] = AUDIO_MODE.DISABLED

    # process the takes
    process_take(take["name"], io_settings, scene_settings, retarget_settings, render_settings)
