import sys
import os
import bpy
import math
import random
from mathutils import Vector
import time
import argparse
import tempfile
from pathlib import Path as myPath
import wave
import numpy as np
import importlib
import csv
import re

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]
sys.path.append(os.path.join(script_dir, "scripts"))

import load_data
importlib.reload(load_data)
import create_scene
importlib.reload(create_scene)
import create_camera
importlib.reload(create_camera)
import create_material
importlib.reload(create_material)
import edit_character
importlib.reload(edit_character)
import edit_audio
importlib.reload(edit_audio)

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
    
def create_sequencer():
    bpy.context.scene.sequence_editor_create()
    
def set_SMPLX_name(filename):
    SMPLX_FILENAME = filename
    
def get_SMPLX_name():
    return SMPLX_FILENAME
    
def set_Output_dir(InOutputDir):
    ARG_OUTPUT_DIR = InOutputDir
    
def get_Output_dir():
    return ARG_OUTPUT_DIR
    
def render_video(output_dir, picture, video, filename_token, actor1, actor2, render_frame_start, render_frame_length, res_x, res_y):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
#    bpy.context.scene.display.shading.light = 'MATCAP'
#    bpy.context.scene.display.render_aa = 'FXAA'
    bpy.context.scene.render.resolution_x=int(res_x)
    bpy.context.scene.render.resolution_y=int(res_y)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = render_frame_start
    bpy.context.scene.frame_set(render_frame_start)
    bpy.context.scene.display.shading.show_specular_highlight = False
    if render_frame_length > 0:
        bpy.context.scene.frame_end = render_frame_start + render_frame_length
    
    main_filepath = os.path.join(output_dir, '{}_main-agent'.format(filename_token))
    # intr_filepath = os.path.join(output_dir, '{}_interloctr.mp4'.format(filename_token))
    # dyad_filepath = os.path.join(output_dir, '{}_dyadic.mp4'.format(filename_token))
    
    if picture:
        bpy.context.scene.render.image_settings.file_format='PNG'
        # create_camera.get_camera('Main_cam')
        # bpy.data.objects[actor1].children[1].hide_render = False
        # bpy.data.objects[actor2].children[1].hide_render = False
        # bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_dyadic_.png'.format(filename_token))
        # bpy.ops.render.render(write_still=True)
        create_camera.get_camera('Main_cam')
#        create_camera.get_camera(actor1 + '_cam')
#        bpy.data.objects[actor1].children[1].hide_render = True
#        bpy.data.objects[actor2].children[1].hide_render = False
        bpy.context.scene.render.filepath = main_filepath
#        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_main-agent_.png'.format(filename_token))
        bpy.ops.render.render(write_still=True)
        # create_camera.get_camera(actor2 + '_cam')
        # bpy.data.objects[actor1].children[1].hide_render = False
        # bpy.data.objects[actor2].children[1].hide_render = True
        # bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_interloctr_.png'.format(filename_token))
        # bpy.ops.render.render(write_still=True)
    
    if video:
        bpy.context.scene.render.image_settings.file_format='MP4'
        print(f"total_frames {render_frame_length}", flush=True)
        bpy.context.scene.render.image_settings.file_format='FFMPEG'
        bpy.context.scene.render.ffmpeg.format='MPEG4'
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.ffmpeg_preset='REALTIME'
        bpy.context.scene.render.ffmpeg.constant_rate_factor='HIGH'
        bpy.context.scene.render.ffmpeg.audio_codec='MP3'
        bpy.context.scene.render.ffmpeg.gopsize = 30
        bpy.context.scene.display.shading.color_type = 'TEXTURE'
        create_camera.get_camera('Main_cam')
#        create_camera.get_camera(actor1 + '_cam')
#        bpy.data.objects[actor1].children[1].hide_render = False
#        bpy.data.objects[actor2].children[1].hide_render = True
        bpy.context.scene.render.filepath = main_filepath
        bpy.ops.render.render(animation=True, write_still=True)
        # create_camera.get_camera(actor2 + '_cam')
        # bpy.data.objects[actor1].children[1].hide_render = True
        # bpy.data.objects[actor2].children[1].hide_render = False
        # bpy.context.scene.render.filepath = intr_filepath
        # bpy.ops.render.render(animation=True, write_still=True)
        # create_camera.get_camera('Main_cam')
        # bpy.data.objects[actor1].children[1].hide_render = False
        # bpy.data.objects[actor2].children[1].hide_render = False
        # bpy.context.scene.render.filepath = dyad_filepath
        # bpy.ops.render.render(animation=True, write_still=True)
    return main_filepath

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-imb', '--input_main_bvh', help='Input filename of the main agent BVH motion file.', type=myPath, required=True)
    parser.add_argument('-iib', '--input_intr_bvh', help='Input filename of the interlocutor BVH motion file', type=myPath, required=True)
    parser.add_argument('-imw', '--input_main_wav', help='Input filename of the main agent WAV audio file.', type=myPath)
    parser.add_argument('-iiw', '--input_intr_wav', help='Input filename of the interlocutor WAV audio file.', type=myPath)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=myPath)
    parser.add_argument('-n', '--output_name', help='The name to use when outputting intermediate and final files. No periods \".\" or slashes \"/\" / \"\\\" allowed.', type=str, required=True)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-r', '--rotate', help='Rotates the character for better positioning in the video frame. Use "cw" for 90-degree clockwise, "ccw" for 90-degree counter-clockwise, "flip" for 180 degree rotation, or leave at "default" for no rotation.', choices=['default', 'cw', 'ccw', 'flip'], type=str, default="default")
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600)
    parser.add_argument('-p', '--png', action='store_true', help='Renders the result in a PNG-formatted image.')
    parser.add_argument('-v', '--video', action='store_true', help='Renders the result in an MP4-formatted video.')
    parser.add_argument('-m', "--visualization_mode", help='The visualization mode to use for rendering.',type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', help='The horizontal resolution for the rendered videos.', type=int, default=1280)
    parser.add_argument('-ry', '--res_y', help='The vertical resolution for the rendered videos.', type=int, default=720)
    parser.add_argument('-sb', '--speechbubble', action='store_true', help='Visualize speaker bubble.')
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

def main():
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
        ##################################
        ##### SET ARGUMENTS MANUALLY #####
        ##### IF RUNNING BLENDER GUI #####
        ##################################
#        ARG_MAIN_BVH_FILE = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_main-agent.bvh'
#        ARG_INTR_BVH_FILE = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_interloctr.bvh'
#        ARG_MAIN_AUDIO_FILE = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_main-agent.wav' # set to None for no audio
#        ARG_INTR_AUDIO_FILE = SCRIPT_DIR / 'test/' / 'val_2023_v0_000_interloctr.wav' # set to None for no audio
        ARG_MAIN_BVH_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/internal/main-agent/bvh/tst_2023_v0_024_main-agent.bvh'
        ARG_INTR_BVH_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/interloctr/bvh/tst_2023_v0_024_interloctr.bvh'
        ARG_MAIN_AUDIO_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/main-agent/wav_norm/tst_2023_v0_024_main-agent.wav' # set to None for no audio
        ARG_INTR_AUDIO_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/interloctr/wav_norm/tst_2023_v0_024_interloctr.wav' # set to None for no audio
        ARG_IMAGE = True
        ARG_VIDEO = False
        ARG_START_FRAME = 322
        ARG_DURATION_IN_FRAMES = 400
        ARG_ROTATE = 'default'
        ARG_RESOLUTION_X = 3840
        ARG_RESOLUTION_Y = 2160
        ARG_RESOLUTION_X = 1280
        ARG_RESOLUTION_Y = 720
        ARG_MODE = 'full_body'
        ARG_BUBBLE = False
        # might need to adjust output directory
        ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        ARG_OUTPUT_NAME = "blender_output_1"
        
        ARG_PLANESIZE = 10
        ARG_LIGHTLOCATION = [0, 5, 15]
        ARG_LIGHTTYPE = 'POINT'
        ARG_LIGHTRADIUS = 2
        ARG_LIGHTPOSITION = [0, 4, 3]
        print('ARG_OUTPUT_DIR: ', ARG_OUTPUT_DIR)
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        ARG_MAIN_BVH_FILE = args['input_main_bvh']
        ARG_INTR_BVH_FILE = args['input_intr_bvh']
        ARG_MAIN_AUDIO_FILE = args['input_main_wav'].resolve() if args['input_main_wav'] else None
        ARG_INTR_AUDIO_FILE = args['input_intr_wav'].resolve() if args['input_intr_wav'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video'] # set to 'False' to get a quick image preview
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_ROTATE = args['rotate']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        ARG_BUBBLE = args['speechbubble']
        # might need to adjust output directory
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else SCRIPT_DIR / 'output/'
        ARG_OUTPUT_NAME = args['output_name']
        
    if ARG_MODE not in ["full_body", "upper_body", "both"]:
        raise NotImplementedError("This visualization mode is not supported ({})!".format(ARG_MODE))
    
    output_dir = ARG_OUTPUT_DIR
    output_name = ARG_OUTPUT_NAME
    assert "." not in output_name, "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in output_name and "\\" not in output_name, "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""

    # FBX file
    FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "GenevaModel_v2_Tpose_Final.fbx")
    MAIN_BVH_NAME = os.path.basename(ARG_MAIN_BVH_FILE).replace('.bvh','')
    INTR_BVH_NAME = os.path.basename(ARG_INTR_BVH_FILE).replace('.bvh','')

    start = time.time()
    
    clear_scene()
    
    SMPLX_FILENAME_IN = get_SMPLX_name()
    SMPLX_FILENAME_IN = "1_wayne_0_73_73"
    
    bpy.ops.object.select_all(action='DESELECT')
    SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/smplxflame_30/'
    SMPLX_TAKE = SMPLX_LOCATION + SMPLX_FILENAME_IN + '.npz'
    bpy.ops.object.smplx_add_animation(filepath=SMPLX_TAKE)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_m_alb.png'
    bpy.ops.object.smplx_set_texture()
    smplx_char = bpy.data.objects[1]
#    smplx_char.rotation_euler[0] = 1.5708 # prevent character from laying
#    smplx_char.rotation_euler[2] = 3.14159 # adjust to camera orientation
#    smplx_char.location[0] = -0.35 # center character
#    smplx_char.location[1] = -0.75 # move character away from camera
    
    root_bone = smplx_char.pose.bones['root']
    pelvis_bone = smplx_char.pose.bones['pelvis']
    
    ARG_DURATION_IN_FRAMES = smplx_char.animation_data.action.frame_range.y
    output_name = smplx_char.name
    
    MAIN_BVH_NAME = smplx_char
    ARG_INTR_BVH_FILE = smplx_char
    
    AUDIO_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/wave16k/'
    ARG_MAIN_AUDIO_FILE = AUDIO_LOCATION + SMPLX_FILENAME_IN + '.wav' # set to None for no audio
#    ARG_INTR_AUDIO_FILE = AUDIO_LOCATION + '10_kieks_0_3_3.wav' # set to None for no audio

#    OBJ1_friendly_name = 'OBJ1'
#    load_data.load_fbx(FBX_MODEL, OBJ1_friendly_name)
#    create_material.add_materials(SCRIPT_DIR, OBJ1_friendly_name)
#    load_data.load_bvh(str(ARG_MAIN_BVH_FILE))
#    edit_character.constraintBoneTargets(armature = OBJ1_friendly_name, rig = MAIN_BVH_NAME, mode = ARG_MODE)
#    
#    OBJ2_friendly_name = 'OBJ2'
#    load_data.load_fbx(FBX_MODEL, OBJ2_friendly_name)
#    create_material.add_materials(SCRIPT_DIR, OBJ2_friendly_name)
#    load_data.load_bvh(str(ARG_INTR_BVH_FILE))
#    edit_character.constraintBoneTargets(armature = OBJ2_friendly_name, rig = INTR_BVH_NAME, mode = ARG_MODE)
#    
#    edit_character.setup_characters(MAIN_BVH_NAME, INTR_BVH_NAME)
    
    create_sequencer()
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    try:
        ARG_MAIN_AUDIO_FILE
    except:
        ARG_MAIN_AUDIO_FILE = ''
        
    try:
        ARG_INTR_AUDIO_FILE
    except:
        ARG_INTR_AUDIO_FILE = ''
    
    if ARG_MAIN_AUDIO_FILE and not IS_SERVER:
        AUDIO1_NAME = os.path.basename(ARG_MAIN_AUDIO_FILE)
        load_data.load_audio(str(ARG_MAIN_AUDIO_FILE), 1)
        audio1 = bpy.data.sounds[AUDIO1_NAME]
        
    if ARG_INTR_AUDIO_FILE and not IS_SERVER:
        AUDIO2_NAME = os.path.basename(ARG_INTR_AUDIO_FILE)
        load_data.load_audio(str(ARG_INTR_AUDIO_FILE), 2)
        audio2 = bpy.data.sounds[AUDIO2_NAME]
    
#    bpy.context.scene.sequence_editor.sequences_all['AudioClip1'].volume = 10
    bpy.context.scene.sequence_editor.sequences_all['AudioClip2'].volume = 0
    
    if not os.path.exists(str(output_dir)):
        os.mkdir(str(output_dir))
    
    framerate = bpy.context.scene.render.fps
    try:
        audio_proc1 = wave.open(os.path.abspath(ARG_MAIN_AUDIO_FILE), 'rb')
    except:
        return
    audio_samples1 = edit_audio.get_volume_strided(audio_proc1, 1 / framerate, -1, -1)
    audio_samples1 = [abs(x) / 32768 for x in audio_samples1] # normalize scale between 0 and 1
    audio_samples1 = [x / max(audio_samples1) for x in audio_samples1] # normalize data between 0 and 1
    audio_samples1 = [0 if x < 0.2 else 1 for x in audio_samples1]
    audio_samples1 = edit_audio.smooth_kernel(audio_samples1, 10)
    audio_samples1 = [max(0.0075, x * 0.05) for x in audio_samples1] # scale down and clamp to min
    
    audio_proc2 = wave.open(os.path.abspath(ARG_INTR_AUDIO_FILE), 'rb')
    audio_samples2 = edit_audio.get_volume_strided(audio_proc2, 1 / framerate, -1, -1)
    audio_samples2 = [abs(x) / 32768 for x in audio_samples2] # normalize scale between 0 and 1
    audio_samples2 = [x / max(audio_samples2) for x in audio_samples2] # normalize data between 0 and 1
    audio_samples2 = [0 if x < 0.2 else 1 for x in audio_samples2]
    audio_samples2 = edit_audio.smooth_kernel(audio_samples2, 10)
    audio_samples2 = [max(0.0075, x * 0.05) for x in audio_samples2] # scale down and clamp to min
    
    if ARG_BUBBLE == True:
        bubble1 = create_scene.add_speechbubble(0.75)
        bubble2 = create_scene.add_speechbubble(-0.75)
        
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
    MAIN_CAM_ROT = [0, 0, 0]
    print(CAM_POS)
    print(pelvis_bone.location)
#    MAIN_CAM_ROT = Vector((pelvis_bone.location[0], pelvis_bone.location[1], pelvis_bone.location[2])) + Vector((0, 0, 0.3)) + Vector((0, -smplx_char.location[1], 0))
    CAM_POS = Vector((pelvis_bone.location[0], pelvis_bone.location[1], pelvis_bone.location[2])) + Vector((0, -0.15, 3))
    print(CAM_POS)
    
#    create_scene.setup_scene(
#        CAM_POS, 
#        MAIN_CAM_ROT, 
#        bpy.data.objects[OBJ1_friendly_name], 
#        bpy.data.objects[OBJ2_friendly_name], 
#        MAIN_BVH_NAME, 
#        INTR_BVH_NAME,
#        ARG_PLANESIZE,
#        ARG_LIGHTLOCATION)
    
    create_scene.setup_scene(
        CAM_POS, 
        MAIN_CAM_ROT, 
        smplx_char, 
        smplx_char, 
        MAIN_BVH_NAME, 
        INTR_BVH_NAME,
        ARG_PLANESIZE,
        ARG_LIGHTLOCATION)
        
    create_scene.add_light(ARG_LIGHTTYPE, ARG_LIGHTRADIUS, ARG_LIGHTPOSITION)
        
#    setup_camera()
        
    total_frames1 = smplx_char.animation_data.action.frame_range.y
    total_frames2 = smplx_char.animation_data.action.frame_range.y
    ARG_DURATION_IN_FRAMES = math.floor(min([ARG_DURATION_IN_FRAMES, total_frames1, total_frames2]))
        
#    main_fp = render_video(
#        str(output_dir), 
#        ARG_IMAGE, 
#        ARG_VIDEO, 
#        output_name, 
#        OBJ1_friendly_name, 
#        OBJ2_friendly_name, 
#        ARG_START_FRAME, 
#        ARG_DURATION_IN_FRAMES, 
#        ARG_RESOLUTION_X, 
#        ARG_RESOLUTION_Y)
        
    main_fp = render_video(
        str(output_dir), 
        ARG_IMAGE, 
        ARG_VIDEO, 
        output_name, 
        smplx_char.name, 
        smplx_char.name, 
        ARG_START_FRAME, 
        ARG_DURATION_IN_FRAMES, 
        ARG_RESOLUTION_X, 
        ARG_RESOLUTION_Y)
    
#     audio1.use_mono = True
#     audio2.use_mono = True
#     bpy.context.scene.sequence_editor.sequences_all['AudioClip1'].pan = 1
#     bpy.context.scene.sequence_editor.sequences_all['AudioClip2'].pan = -1
    
#     bvh1_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input1', filepath=intr_fp, channel=3, frame_start=ARG_START_FRAME)
#     bvh1_mp4.mute = True
#     bvh1_mp4.use_proxy = False
#     input1_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input1_effect', type='TRANSFORM', channel=4, frame_start=ARG_START_FRAME, seq1=bvh1_mp4)
#     input1_effect.use_uniform_scale = True
#     input1_effect.transform.offset_x = -350
#     input1_effect.transform.offset_y = 30
#     input1_effect.transform.scale_y = 1.000001
#     input1_effect.blend_type = 'ALPHA_OVER'
#     input1_effect.crop.max_x = 300
#     input1_effect.crop.min_x = 300
    
#     bvh2_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input2', filepath=main_fp, channel=5, frame_start=ARG_START_FRAME)
#     bvh2_mp4.mute = True
#     bvh2_mp4.use_proxy = False
#     input2_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input2_effect', type='TRANSFORM', channel=6, frame_start=ARG_START_FRAME, seq1=bvh2_mp4)
#     input2_effect.use_uniform_scale = True
#     input2_effect.transform.offset_x = 350
#     input2_effect.transform.offset_y = 30
#     input2_effect.transform.scale_y = 1.000001
#     input2_effect.blend_type = 'ALPHA_OVER'
#     input2_effect.crop.max_x = 300
#     input2_effect.crop.min_x = 300
    
#     main_mp4 = bpy.context.scene.sequence_editor.sequences.new_movie(name='input3', filepath=dyad_fp, channel=7, frame_start=ARG_START_FRAME)
#     main_mp4.mute = True
#     main_mp4.use_proxy = False
#     input3_effect = bpy.context.scene.sequence_editor.sequences.new_effect(name='input3_effect', type='TRANSFORM', channel=8, frame_start=ARG_START_FRAME, seq1=main_mp4)
#     input3_effect.use_uniform_scale = True
#     input3_effect.scale_start_x = 0.225
#     input3_effect.transform.offset_x = 0
#     input3_effect.transform.offset_y = -249
#     input3_effect.blend_type = 'ALPHA_OVER'
# #    input3_effect.color_multiply = 1.05
#     input3_effect.crop.max_y = 0
#     input3_effect.crop.min_y = 0
#     input3_effect.crop.max_x = 450
#     input3_effect.crop.min_x = 450
    
#     text_actor1 = bpy.context.scene.sequence_editor.sequences.new_effect(name='Main_Agent',type='TEXT', channel=9, frame_start=ARG_START_FRAME, frame_end=ARG_START_FRAME + ARG_DURATION_IN_FRAMES + 1)
#     text_actor1.font_size = 30
#     text_actor1.location[0] = 0.92
#     text_actor1.location[1] = 0.11
#     text_actor1.text = "Main Agent"
    
#     text_actor2 = bpy.context.scene.sequence_editor.sequences.new_effect(name='Interlocutor',type='TEXT', channel=10, frame_start=ARG_START_FRAME, frame_end=ARG_START_FRAME + ARG_DURATION_IN_FRAMES + 1)
#     text_actor2.font_size = 30
#     text_actor2.location[0] = 0.10
#     text_actor2.location[1] = 0.11
#     text_actor2.text = "Interlocutor"
    
#    if ARG_VIDEO == True:
#        seq_filepath = os.path.join(str(output_dir), f'{output_name}.mp4')
#        bpy.context.scene.render.filepath = seq_filepath
#        bpy.context.scene.render.resolution_y = ARG_RESOLUTION_Y + 50
#        bpy.ops.render.render(animation=True)
#    
#    if ARG_IMAGE == True:
#        bpy.context.scene.render.image_settings.file_format='PNG'
#        seq_filepath = os.path.join(str(output_dir), f'{output_name}.png')
#        bpy.context.scene.render.filepath = seq_filepath
#        bpy.context.scene.render.resolution_y = ARG_RESOLUTION_Y + 50
#        bpy.ops.render.render(write_still=True)
    
    end = time.time()
    all_time = end - start
    print("output_file", str(list(output_dir.glob("*"))[0]), flush=True)
    print(all_time)


#Code line
#SMPLX_FILENAME = '28_tiffnay_0_2_2'
#main()

def extract_segment(file_name):
    try:
        # Remove the file extension
        base_name = file_name.rsplit('.', 1)[0]
#        print(base_name)
        # Split by underscores
        parts = base_name.split('_')
#        print(parts)
        # Extract the required segment
        result = '_'.join(parts[2:7])  # Indices 1 to 5 (inclusive)
        return result
    except IndexError:
        print("Error: The filename format doesn't match the expected convention.")
        return None

def filter_csv_by_type(file_path, match_type="test"):
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            result = [row['id'] for row in reader if row['type'] == match_type]
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []

SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
file_path = 'S://Work//GENEA//GENEA2024//beat_v2.0.0//beat_english_v2.0.0//train_test_split.csv'
ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'

# Call the function and print the results
matches = filter_csv_by_type(file_path)
#print("Matches from the 1st column where 'type' is 'test':")
#print(matches)

for File in matches:
    SMPLX_FILENAME = File
    print(File)
#    set_SMPLX_name(File)
#    print(get_SMPLX_name())
    
    for Output_File in list(ARG_OUTPUT_DIR.glob("*")):
#       print(Output_File)
        segment = extract_segment(str(Output_File))
        if segment in File:
#           print("Extracted segment:", segment)
            print(Output_File.stem)
#            main()
    
#print(len(str(list(ARG_OUTPUT_DIR.glob("*"))[0])))
#print(str(list(ARG_OUTPUT_DIR.glob("*"))))
#output_directory = str(list(ARG_OUTPUT_DIR.glob("*")))

# Call the function and print results
#segments = extract_segments(output_directory)
#print("Extracted segments:", segments)

#for Output_File in list(ARG_OUTPUT_DIR.glob("*")):
##    print(Output_File)
#    segment = extract_segment(str(Output_File))
#    if segment not in matches:
##        print("Extracted segment:", segment)
#        print(Output_File.stem)
    
main()