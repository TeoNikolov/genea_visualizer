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

from bpy.app.handlers import persistent

@persistent
def load_handler(dummy):
    print("Load Handler:", bpy.data.filepath)

bpy.app.handlers.load_post.append(load_handler)

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
    
def render_video(output_dir, picture, video, filename_token, render_frame_start, render_frame_length, res_x, res_y):
    scene = bpy.context.scene
    render = scene.render
    
    render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    render.resolution_x=int(res_x)
    render.resolution_y=int(res_y)
    render.fps = 30
    scene.frame_start = render_frame_start
    scene.frame_set(render_frame_start)
    scene.display.shading.show_specular_highlight = False
    render.image_settings.color_depth = '16'
    
    if render_frame_length > 0:
        scene.frame_end = render_frame_start + render_frame_length
    
    main_filepath = os.path.join(output_dir, '{}_main-agent'.format(filename_token))
    
    if picture:
        render.image_settings.file_format='PNG'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(write_still=True)
    
    if video:
        render.image_settings.file_format='MP4'
        print(f"total_frames {render_frame_length}", flush=True)
        render.image_settings.file_format='FFMPEG'
        render.ffmpeg.format='MPEG4'
        render.ffmpeg.codec = "H264"
        render.ffmpeg.ffmpeg_preset='REALTIME'
        render.ffmpeg.constant_rate_factor='HIGH'
        render.ffmpeg.audio_codec='MP3'
        render.ffmpeg.gopsize = 30
        scene.display.shading.color_type = 'TEXTURE'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(animation=True, write_still=True)
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
    start = time.time()
    clear_scene()
    
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
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 100
        ARG_RESOLUTION_X = 1280 #3840
        ARG_RESOLUTION_Y = 720 #2160
        ARG_MODE = 'full_body'
        ARG_BUBBLE = False
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
        args = parse_args()
        ARG_MAIN_BVH_FILE = args['input_main_bvh']
        ARG_INTR_BVH_FILE = args['input_intr_bvh']
        ARG_MAIN_AUDIO_FILE = args['input_main_wav'].resolve() if args['input_main_wav'] else None
        ARG_INTR_AUDIO_FILE = args['input_intr_wav'].resolve() if args['input_intr_wav'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video']
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        ARG_BUBBLE = args['speechbubble']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else SCRIPT_DIR / 'output/'
        ARG_OUTPUT_NAME = args['output_name']
    
    output_dir = ARG_OUTPUT_DIR
    
    if not os.path.exists(str(output_dir)):
        os.mkdir(str(output_dir))
    
    output_name = ARG_OUTPUT_NAME
    assert "." not in output_name, "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in output_name and "\\" not in output_name, "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    SMPLX_FILENAME_IN = "1_wayne_0_73_73"
    
    bpy.ops.object.select_all(action='DESELECT')
    SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/smplxflame_30/'
    SMPLX_TAKE = SMPLX_LOCATION + SMPLX_FILENAME_IN + '.npz'
    bpy.ops.object.smplx_add_animation(filepath=SMPLX_TAKE)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_m_alb.png'
    bpy.ops.object.smplx_set_texture()
    smplx_char = bpy.data.objects[1]
    
    root_bone = smplx_char.pose.bones['root']
    pelvis_bone = smplx_char.pose.bones['pelvis']
    
    ARG_DURATION_IN_FRAMES = smplx_char.animation_data.action.frame_range.y
    output_name = smplx_char.name
    
    AUDIO_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/wave16k/'
    ARG_MAIN_AUDIO_FILE = AUDIO_LOCATION + SMPLX_FILENAME_IN + '.wav' # set to None for no audio
    
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
    
    framerate = bpy.context.scene.render.fps
    
    audio_samples1 = edit_audio.load_and_fix_audio(ARG_MAIN_AUDIO_FILE, framerate)
    audio_samples2 = edit_audio.load_and_fix_audio(ARG_INTR_AUDIO_FILE, framerate)
    
    if ARG_BUBBLE == True:
        bubble1 = create_scene.add_speechbubble(0.75)
        bubble2 = create_scene.add_speechbubble(-0.75)
        
        for i in range(ARG_DURATION_IN_FRAMES):
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
                
    blend_file_path = "S:/Work/GENEA2022/GENEA2023VIZoutput/IndoorEnvironment_tilted.blend"
    
    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)  # Load all available objects

    # Link the imported objects to the active collection
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            
    MAIN_CAM_ROT = [0, 0, 0]
    CAM_POS = Vector((
        pelvis_bone.location[0], 
        pelvis_bone.location[1], 
        pelvis_bone.location[2])) + Vector((0, -0.15, 4))
    
    create_scene.setup_scene(
        CAM_POS,
        MAIN_CAM_ROT,
        ARG_PLANESIZE,
        ARG_LIGHTLOCATION)
        
#    create_scene.add_light(ARG_LIGHTTYPE, ARG_LIGHTRADIUS, ARG_LIGHTPOSITION)

    bpy.ops.object.select_all(action='DESELECT')
    
    smplx_char.select_set(True)
    mainCam = bpy.data.objects['Main_cam']
    mainCam.select_set(True)
    
    bpy.ops.transform.rotate(value=-1.57, orient_axis='X')
        
    total_frames1 = smplx_char.animation_data.action.frame_range.y
    total_frames2 = smplx_char.animation_data.action.frame_range.y
    ARG_DURATION_IN_FRAMES = math.floor(min([ARG_DURATION_IN_FRAMES, total_frames1, total_frames2]))
        
    main_fp = render_video(
        str(output_dir), 
        ARG_IMAGE, 
        ARG_VIDEO, 
        output_name,
        ARG_START_FRAME, 
        ARG_DURATION_IN_FRAMES, 
        ARG_RESOLUTION_X, 
        ARG_RESOLUTION_Y)
    
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
    # SMPLX_FILENAME = File
    print(File)
    # set_SMPLX_name(File)
    # print(get_SMPLX_name())
    
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