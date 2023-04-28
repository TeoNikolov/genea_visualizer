import sys
import os
import bpy
import math
import random
from mathutils import Vector
import time
import argparse
import tempfile
from pathlib import Path
import wave
import numpy as np

# cleans up the scene and memory
def clear_scene():
    for block in bpy.data.meshes:       bpy.data.meshes.remove(block)
    for block in bpy.data.materials:    bpy.data.materials.remove(block)
    for block in bpy.data.textures:     bpy.data.textures.remove(block)
    for block in bpy.data.images:       bpy.data.images.remove(block)  
    for block in bpy.data.curves:       bpy.data.curves.remove(block)
    for block in bpy.data.cameras:      bpy.data.cameras.remove(block)
    for block in bpy.data.lights:       bpy.data.lights.remove(block)
    for block in bpy.data.sounds:       bpy.data.sounds.remove(block)
    for block in bpy.data.armatures:    bpy.data.armatures.remove(block)
    for block in bpy.data.objects:      bpy.data.objects.remove(block)
    for block in bpy.data.actions:      bpy.data.actions.remove(block)
            
    if bpy.context.object == None:          bpy.ops.object.delete()
    elif bpy.context.object.mode == 'EDIT': bpy.ops.object.mode_set(mode='OBJECT')
    elif bpy.context.object.mode == 'POSE': bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
    
def setup_scene(cam_pos, cam_rot, actor1, actor2, arm1, arm2, plane_size=5):
    
    # Camera Main
    name = 'Main'
    add_camera(cam_pos, cam_rot, name)
    
    # Camera actor 1
    actor1c = actor1.children[0]
    actor1c.name = 'actor1_loc'
    arm1 = bpy.data.objects[arm1]
    
    # Camera actor 2
    actor2c = actor2.children[0]
    actor2c.name = 'actor2_loc'
    arm2 = bpy.data.objects[arm2]
    
    cam_pos = [0, 0.75, 1.5]
    cam_rot = [math.radians(80), 0, math.radians(180)]
    add_camera(cam_pos, cam_rot, actor2.name)
    
    cam_pos = [0, -0.75, 1.5]
    cam_rot = [math.radians(80), 0, 0]
    add_camera(cam_pos, cam_rot, actor1.name)
    
    add_plane(plane_size)

    # Sky Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=256, radius=75)
    sky_obj = bpy.data.objects['Sphere']
    sky_obj.name = 'Sky'
    sky_mat = bpy.data.materials.new(name="SkyColor")
    sky_mat.diffuse_color = (0.115, 0.25, 0.3, 1)
    sky_obj.data.materials.append(sky_mat) #add the material to the object

def add_plane(prov_size):
    bpy.ops.mesh.primitive_plane_add(size=prov_size)
    plane_obj = bpy.data.objects['Plane']
    plane_obj.name = 'Floor'
    plane_obj.scale[0] = 2.3
    plane_obj.scale[1] = 2.175
    mat = bpy.data.materials['FloorColor'] #set new material to variable
    mat.diffuse_color = (0.115, 0.25, 0.3, 1)
    plane_obj.data.materials.append(mat) #add the material to the object
    
def add_speechbubble(y):
    bpy.ops.mesh.primitive_uv_sphere_add()
    bub_obj = bpy.data.objects['Sphere']
    bub_obj.name = 'SpeechBubble'
    bub_obj.location[0] = 0
    bub_obj.location[1] = y
    bub_obj.location[2] = 1.85
    mat = bpy.data.materials['FloorColor'] #set new material to variable
    mat.diffuse_color = (0.115, 0.25, 0.3, 1)
    bub_obj.data.materials.append(mat) #add the material to the object
    return bub_obj
    
def add_camera(cam_pos, cam_rot, name):
    bpy.ops.object.camera_add(enter_editmode=False, location=cam_pos, rotation=cam_rot)
    cam = bpy.data.objects['Camera']
    cam.scale = [5, 25, 5]
    cam.data.lens = 17.5
    if name == 'Main':
        cam.data.lens = 35
    cam.name = name + '_cam'
    bpy.context.scene.camera = cam # add cam so it's rendered
    
def setup_characters(actor1, actor2):
    arm1 = bpy.context.scene.objects[actor1]
    arm2 = bpy.context.scene.objects[actor2]
    arm1.location = [0, 0.75, 0]
    arm2.location = [0, 0.75, 0]

    
def get_camera(name):
    cam = bpy.data.objects[name]
    bpy.context.scene.camera = cam

def remove_bone(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones: # deselect the other bones
        if bone.name == bone_name:
            armature.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_fbx(filepath, name):
    bpy.ops.import_scene.fbx(filepath=filepath, ignore_leaf_bones=True, 
    force_connect_children=True, automatic_bone_orientation=False)
    remove_bone(bpy.data.objects['Armature'], 'b_r_foot_End')
    bpy.data.objects['Armature'].name = name
        
def load_bvh(filepath):
    bpy.ops.import_anim.bvh(filepath=filepath, use_fps_scale=False,
    update_scene_fps=True, update_scene_duration=True, global_scale=0.01)

def add_materials(work_dir, name):
    mat = bpy.data.materials.new('gray')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(os.path.join(work_dir, 'model', "LowP_03_Texture_ColAO_grey5.jpg"))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    obj = bpy.data.objects['LowP_01']
    obj.modifiers['Armature'].use_deform_preserve_volume=True
    # Assign it to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # set new material to variable
    mat = bpy.data.materials.new(name="FloorColor")
    mat.diffuse_color = (0.15, 0.4, 0.25, 1)
    
def constraintBoneTargets(armature = 'Armature', rig = 'None', mode = 'full_body'):
    armobj = bpy.data.objects[armature]
    for ob in bpy.context.scene.objects: ob.select_set(False)
    bpy.context.view_layer.objects.active = armobj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    for bone in bpy.context.selected_pose_bones:
        # Delete all other constraints
        for c in bone.constraints:
            bone.constraints.remove( c )
        # Create body_world location to fix floating legs
        if bone.name == 'body_world' and mode == 'full_body':
            constraint = bone.constraints.new('COPY_LOCATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
        # Create all rotations
        if bpy.context.scene.objects[armature].data.bones.get(bone.name) is not None:
            constraint = bone.constraints.new('COPY_ROTATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
    if mode == 'upper_body':
        bpy.context.object.pose.bones["b_root"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_leg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_leg"].constraints["Copy Rotation"].mute = True
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_audio(filepath, name):
    bpy.context.scene.sequence_editor_create()
    bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip' + str(name),
        filepath=filepath,
        channel=name,
        frame_start=0
    )
    
def render_video(output_dir, picture, video, bvh1_fname, bvh2_fname, actor1, actor2, render_frame_start, render_frame_length, res_x, res_y):
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.display.shading.light = 'MATCAP'
    bpy.context.scene.display.render_aa = 'FXAA'
    bpy.context.scene.render.resolution_x=int(res_x)
    bpy.context.scene.render.resolution_y=int(res_y)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = render_frame_start
    bpy.context.scene.frame_set(render_frame_start)
    if render_frame_length > 0:
        bpy.context.scene.frame_end = render_frame_start + render_frame_length
    
    if picture:
        bpy.context.scene.render.image_settings.file_format='PNG'
        get_camera('Main_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, 'Main_{}_.png'.format(bvh1_fname))
        bpy.ops.render.render(write_still=True)
        get_camera(actor1 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = True
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_.png'.format(bvh1_fname))
        bpy.ops.render.render(write_still=True)
        get_camera(actor2 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = True
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_.png'.format(bvh2_fname))
        bpy.ops.render.render(write_still=True)
    
    BVH1_filepath = os.path.join(output_dir, '{}.mp4'.format(bvh1_fname))
    BVH2_filepath = os.path.join(output_dir, '{}.mp4'.format(bvh2_fname))
    Main_filepath = os.path.join(output_dir, 'Main_{}.mp4'.format(bvh1_fname))
    
    if video:
        print(f"total_frames {render_frame_length}", flush=True)
        bpy.context.scene.render.image_settings.file_format='FFMPEG'
        bpy.context.scene.render.ffmpeg.format='MPEG4'
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.ffmpeg_preset='REALTIME'
        bpy.context.scene.render.ffmpeg.constant_rate_factor='HIGH'
        bpy.context.scene.render.ffmpeg.audio_codec='MP3'
        bpy.context.scene.render.ffmpeg.gopsize = 30
        get_camera(actor2 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = True
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath = BVH1_filepath
        bpy.ops.render.render(animation=True, write_still=True)
        get_camera(actor1 + '_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = True
        bpy.context.scene.render.filepath = BVH2_filepath
        bpy.ops.render.render(animation=True, write_still=True)
        get_camera('Main_cam')
        bpy.data.objects[actor1].children[1].hide_render = False
        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath = Main_filepath
        bpy.ops.render.render(animation=True, write_still=True)
    return Main_filepath, BVH1_filepath, BVH2_filepath

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i1', '--input1', help='Input file name of the first BVH to render.', type=Path, required=True)
    parser.add_argument('-i2', '--input2', help='Input file name of the second BVH to render.', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-r', '--rotate', help='Rotates the character for better positioning in the video frame. Use "cw" for 90-degree clockwise, "ccw" for 90-degree counter-clockwise, "flip" for 180 degree rotation, or leave at "default" for no rotation.', choices=['default', 'cw', 'ccw', 'flip'], type=str, default="default")
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600)
    parser.add_argument('-a1', '--input_audio1', help='Input file name of the first audio clip to include in the final render.', type=Path)
    parser.add_argument('-a2', '--input_audio2', help='Input file name of the second audio clip to include in the final render.', type=Path)
    parser.add_argument('-p', '--png', action='store_true', help='Renders the result in a PNG-formatted image.')
    parser.add_argument('-v', '--video', action='store_true', help='Renders the result in an MP4-formatted video.')
    parser.add_argument('-m', "--visualization_mode", help='The visualization mode to use for rendering.',type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', help='The horizontal resolution for the rendered videos.', type=int, default=1280)
    parser.add_argument('-ry', '--res_y', help='The vertical resolution for the rendered videos.', type=int, default=720)  
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

def read_audio_strided(audio, stride, start, stop):
    rate = audio.getframerate()
    if start < 0: start = 0 # seconds
    if stop  < 0: stop  = audio.getnframes() / rate # seconds
    stop     = math.floor(stop * rate)     # samples
    start    = math.floor(start * rate)    # samples
    stride   = math.floor(stride * rate)   # samples
    if start > audio.getnframes(): start = audio.getnframes() - 1
    if stop  > audio.getnframes(): stop  = audio.getnframes()
    duration = stop - start # samples

    data = []
    sample_count = math.ceil(duration / stride) # samples
    positions = [start + stride * i for i in range(sample_count)]
    for p in positions:
        if p >= audio.getnframes():
            break
        audio.setpos(p)
        sample = np.frombuffer(audio.readframes(1), dtype=np.int16)[0]
        data.append(sample)
    return data

def get_volume(audio, time):
    volume = -1
    time_range = 0.01 # 220 samples (110 before, 110 after)
    stride = 0.001 # 22 samples
    samples = read_audio_strided(audio, stride, time - time_range, time + time_range)
    samples = [abs(x) for x in samples] # absolute
    volume = max(samples)
    return volume

def get_volume_strided(audio, stride, start, stop):
    if start < 0: start = 0
    if stop  < 0: stop = audio.getnframes() / audio.getframerate()
    times = []
    v = start
    i = 0
    while v < stop:
        v = start + stride * i
        times.append(v)
        i += 1
    volumes = [get_volume(audio, t) for t in times]
    return volumes

def smooth_kernel(data, offset=5):
    out_data = []
    for i in range(len(data)):
        start = max(0, i - offset)
        stop = min(len(data), i + offset + 1)
        out_data.append(data[i])
        for j in range(start, stop):
            if data[j] > 0:
                out_data[-1] = 1
                break
    return out_data

def main():
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = Path(bpy.context.space_data.text.filepath).parents[0]
        ##################################
        ##### SET ARGUMENTS MANUALLY #####
        ##### IF RUNNING BLENDER GUI #####
        ##################################
        ARG_BVH1_PATHNAME = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_main-agent.bvh'
        ARG_BVH2_PATHNAME = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_interloctr.bvh'
        ARG_AUDIO_FILE_NAME1 = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_main-agent.wav' # set to None for no audio
        ARG_AUDIO_FILE_NAME2 = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_interloctr.wav' # set to None for no audio
        ARG_IMAGE = False
        ARG_VIDEO = True
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 600
        ARG_ROTATE = 'default'
        ARG_RESOLUTION_X = 1280
        ARG_RESOLUTION_Y = 720
        ARG_MODE = 'full_body'
        # might need to adjust output directory
        ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/'
        print('ARG_OUTPUT_DIR: ', ARG_OUTPUT_DIR)
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = Path(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        ARG_BVH1_PATHNAME = args['input1']
        ARG_BVH2_PATHNAME = args['input2']
        ARG_AUDIO_FILE_NAME1 = args['input_audio1'].resolve() if args['input_audio1'] else None
        ARG_AUDIO_FILE_NAME2 = args['input_audio2'].resolve() if args['input_audio2'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video'] # set to 'False' to get a quick image preview
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_ROTATE = args['rotate']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        # might need to adjust output directory
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else SCRIPT_DIR / 'output/'
        
    if ARG_MODE not in ["full_body", "upper_body", "both"]:
        raise NotImplementedError("This visualization mode is not supported ({})!".format(ARG_MODE))
    
    # FBX file
    FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "GenevaModel_v2_Tpose_Final.fbx")
    BVH1_NAME = os.path.basename(ARG_BVH1_PATHNAME).replace('.bvh','')
    BVH2_NAME = os.path.basename(ARG_BVH2_PATHNAME).replace('.bvh','')
    AUDIO1_NAME = os.path.basename(ARG_AUDIO_FILE_NAME1)
    AUDIO2_NAME = os.path.basename(ARG_AUDIO_FILE_NAME2)

    start = time.time()
    
    clear_scene()
    
    OBJ1_friendly_name = 'OBJ1'
    load_fbx(FBX_MODEL, OBJ1_friendly_name)
    add_materials(SCRIPT_DIR, OBJ1_friendly_name)
    load_bvh(str(ARG_BVH1_PATHNAME))
    constraintBoneTargets(armature = OBJ1_friendly_name, rig = BVH1_NAME, mode = ARG_MODE)
    
    OBJ2_friendly_name = 'OBJ2'
    load_fbx(FBX_MODEL, OBJ2_friendly_name)
    add_materials(SCRIPT_DIR, OBJ2_friendly_name)
    load_bvh(str(ARG_BVH2_PATHNAME))
    constraintBoneTargets(armature = OBJ2_friendly_name, rig = BVH2_NAME, mode = ARG_MODE)
    
    setup_characters(BVH1_NAME,BVH2_NAME)
    
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    try:
        ARG_AUDIO_FILE_NAME1
    except:
        ARG_AUDIO_FILE_NAME1 = ''
        
    try:
        ARG_AUDIO_FILE_NAME2
    except:
        ARG_AUDIO_FILE_NAME2 = ''
        
    if ARG_AUDIO_FILE_NAME1 and not IS_SERVER:
        load_audio(str(ARG_AUDIO_FILE_NAME1), 1)
        audio1 = bpy.data.sounds[AUDIO1_NAME]
        
    if ARG_AUDIO_FILE_NAME2 and not IS_SERVER:
        load_audio(str(ARG_AUDIO_FILE_NAME2), 2)
        audio2 = bpy.data.sounds[AUDIO2_NAME]
    
    bpy.context.scene.sequence_editor.sequences_all['AudioClip1'].volume = 20
    bpy.context.scene.sequence_editor.sequences_all['AudioClip2'].volume = 20
    
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
    
    framerate = bpy.context.scene.render.fps
    audio_proc1 = wave.open(os.path.abspath(ARG_AUDIO_FILE_NAME1), 'rb')
    audio_samples1 = get_volume_strided(audio_proc1, 1 / framerate, -1, -1)
    audio_samples1 = [abs(x) / 32768 for x in audio_samples1] # normalize scale between 0 and 1
    audio_samples1 = [x / max(audio_samples1) for x in audio_samples1] # normalize data between 0 and 1
    audio_samples1 = [0 if x < 0.2 else 1 for x in audio_samples1]
    audio_samples1 = smooth_kernel(audio_samples1, 10)
    audio_samples1 = [max(0.0075, x * 0.05) for x in audio_samples1] # scale down and clamp to min
    
    audio_proc2 = wave.open(os.path.abspath(ARG_AUDIO_FILE_NAME2), 'rb')
    audio_samples2 = get_volume_strided(audio_proc2, 1 / framerate, -1, -1)
    audio_samples2 = [abs(x) / 32768 for x in audio_samples2] # normalize scale between 0 and 1
    audio_samples2 = [x / max(audio_samples2) for x in audio_samples2] # normalize data between 0 and 1
    audio_samples2 = [0 if x < 0.2 else 1 for x in audio_samples2]
    audio_samples2 = smooth_kernel(audio_samples2, 10)
    audio_samples2 = [max(0.0075, x * 0.05) for x in audio_samples2] # scale down and clamp to min
    
    bubble1 = add_speechbubble(0.75)
    bubble2 = add_speechbubble(-0.75)
    
    for i in range(ARG_DURATION_IN_FRAMES):
        start_frame = i * framerate
        end_frame = (i + 1) * framerate
        if i < len(audio_samples1):
            a1s = audio_samples1[i]
            a2s = audio_samples2[i]
        else:
            a1s = audio_samples1[-1]
            a2s = audio_samples2[-1]
        
        bubble1.scale = (a1s, a1s, a1s)
        bubble1.keyframe_insert(data_path='scale', frame=i)
        
        bubble2.scale = (a2s, a2s, a2s)
        bubble2.keyframe_insert(data_path='scale', frame=i)
      
    # 05/04/2023 fix main camera orientation, fix character rotation and personal cameras
    if ARG_MODE == "full_body":     CAM_POS = [3.25, 0, 1.8]
    elif ARG_MODE == "upper_body":  CAM_POS = [0, -2.45, 1.3]
    MAIN_CAM_ROT = [math.radians(80), 0, math.radians(90)]
    setup_scene(CAM_POS, MAIN_CAM_ROT, bpy.data.objects[OBJ1_friendly_name], bpy.data.objects[OBJ2_friendly_name], BVH1_NAME, BVH2_NAME)
        
    total_frames1 = bpy.data.objects[BVH1_NAME].animation_data.action.frame_range.y
    total_frames2 = bpy.data.objects[BVH2_NAME].animation_data.action.frame_range.y
    ARG_DURATION_IN_FRAMES = min([ARG_DURATION_IN_FRAMES, total_frames1, total_frames2])        
    main_fp, bvh1_fp, bvh2_fp = render_video(str(ARG_OUTPUT_DIR), ARG_IMAGE, ARG_VIDEO, BVH1_NAME, BVH2_NAME, OBJ1_friendly_name, OBJ2_friendly_name, ARG_START_FRAME, ARG_DURATION_IN_FRAMES, ARG_RESOLUTION_X, ARG_RESOLUTION_Y)
    
    audio1.use_mono = True
    audio2.use_mono = True
    bpy.context.scene.sequence_editor.sequences_all['AudioClip1'].pan = 1
    bpy.context.scene.sequence_editor.sequences_all['AudioClip2'].pan = -1
    
    bvh1_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input1', filepath=bvh1_fp, channel=3, frame_start=0)
    bvh1_mp4.mute = True
    bvh1_mp4.use_proxy = False
    input1_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input1_effect', type='TRANSFORM', channel=4, frame_start=0, seq1=bvh1_mp4)
    input1_effect.use_uniform_scale = True
    input1_effect.transform.offset_x = -350
    input1_effect.transform.offset_y = 0
    input1_effect.transform.scale_y = 1.000001
    input1_effect.blend_type = 'ALPHA_OVER'
    input1_effect.crop.max_x = 300
    input1_effect.crop.min_x = 300
    
    bvh2_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input2', filepath=bvh2_fp, channel=5, frame_start=0)
    bvh2_mp4.mute = True
    bvh2_mp4.use_proxy = False
    input2_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input2_effect', type='TRANSFORM', channel=6, frame_start=0, seq1=bvh2_mp4)
    input2_effect.use_uniform_scale = True
    input2_effect.transform.offset_x = 350
    input2_effect.transform.offset_y = 0
    input2_effect.transform.scale_y = 1.000001
    input2_effect.blend_type = 'ALPHA_OVER'
    input2_effect.crop.max_x = 300
    input2_effect.crop.min_x = 300
    
    main_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input3', filepath=main_fp, channel=7, frame_start=0)
    main_mp4.mute = True
    main_mp4.use_proxy = False
    input3_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input3_effect', type='TRANSFORM', channel=8, frame_start=0, seq1=main_mp4)
    input3_effect.use_uniform_scale = True
    input3_effect.scale_start_x = 0.225
    input3_effect.transform.offset_x = 0
    input3_effect.transform.offset_y = -279
    input3_effect.blend_type = 'ALPHA_OVER'
#    input3_effect.color_multiply = 1.05
    input3_effect.crop.max_y = 0
    input3_effect.crop.min_y = 0
    input3_effect.crop.max_x = 450
    input3_effect.crop.min_x = 450
    
    text_actor1 = bpy.context.scene.sequence_editor.sequences.new_effect(name='Main_Agent',type='TEXT', channel=9, frame_start=0, frame_end=ARG_DURATION_IN_FRAMES + 1)
    text_actor1.font_size = 30
    text_actor1.location[0] = 0.92
    text_actor1.location[1] = 0.04
    text_actor1.text = "Main Agent"
    
    text_actor2 = bpy.context.scene.sequence_editor.sequences.new_effect(name='Interlocutor',type='TEXT', channel=10, frame_start=0, frame_end=ARG_DURATION_IN_FRAMES + 1)
    text_actor2.font_size = 30
    text_actor2.location[0] = 0.10
    text_actor2.location[1] = 0.04
    text_actor2.text = "Interlocutor"
    
    if ARG_VIDEO == True:
        seq_filepath = os.path.join(str(ARG_OUTPUT_DIR), 'Sequence.mp4')
        bpy.context.scene.render.filepath = seq_filepath
        bpy.ops.render.render(animation=True)
    
    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    print(all_time)

#Code line
main()
