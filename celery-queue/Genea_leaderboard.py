import sys
import os
import bpy
from mathutils import Vector
import time
import tempfile
from pathlib import Path as myPath
import numpy as np
import importlib
import re
import tempfile

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
import parser
importlib.reload(parser)

def render_video(output_dir, framerate, picture, video, filename_token, render_frame_start, render_frame_length, res_x, res_y):
    main_filepath = ''
    
    scene = bpy.context.scene
    render = scene.render
    
    render.engine = 'CYCLES'
    render.resolution_x=int(res_x)
    render.resolution_y=int(res_y)
    
    render.fps = framerate
    render.frame_map_new = 100
    
    if framerate == 24:
        render.frame_map_new = 80
    
    scene.frame_start = render_frame_start
    scene.frame_set(render_frame_start)
    
    if render.engine == 'WORKBENCH':
        scene.display.shading.show_specular_highlight = False
    
    if render.engine == 'CYCLES': #Defaults
        scene.cycles.device = 'GPU' #CPU
        render.compositor_device = 'GPU'
        scene.cycles.samples = 8 #4096
        scene.cycles.time_limit = 0 #0
        scene.cycles.adaptive_threshold = 0.025 #0.01
        scene.cycles.use_denoising = True
        scene.cycles.denoising_use_gpu = True
        scene.cycles.denoising_prefilter = 'ACCURATE' #ACCURATE #FAST
        scene.cycles.denoising_quality = 'FAST' #HIGH #BALANCED #FAST
        scene.cycles.max_bounces = 0 #12
        scene.cycles.diffuse_bounces = 0 #4
        scene.cycles.glossy_bounces = 0 #4
        scene.cycles.transmission_bounces = 0 #12
        scene.cycles.transparent_max_bounces = 0 #8
        scene.cycles.volume_max_steps = 256 #1024
        render.use_persistent_data = True #False
        scene.world.cycles.sampling_method = 'MANUAL' #AUTO
        scene.world.cycles.sample_map_resolution = 1024 #1024
        scene.world.cycles.max_bounces = 1 #1024
        scene.cycles.use_fast_gi = True #False
        scene.cycles.ao_bounces_render = 1 #1
        scene.world.light_settings.distance = 2 #10
        
        render.use_simplify = False #False
        # scene.cycles.texture_limit_render = 'OFF' #OFF
        # render.simplify_child_particles_render = 1 #1
        # render.simplify_subdivision_render = 6 #6
        
        scene.cycles.use_auto_tile = True #True
        # scene.cycles.tile_size = 1024 #1024
    
    if render_frame_length > 0:
        scene.frame_end = render_frame_start + int(render_frame_length * (render.frame_map_new / 100))
    
    if picture:
        main_filepath = os.path.join(output_dir, '{}'.format(filename_token))
        render.image_settings.file_format='PNG'
        render.image_settings.color_depth = '16'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(write_still=True)
    
    if video:
        main_filepath = os.path.join(output_dir, '{}_'.format(filename_token))
        render.image_settings.file_format='FFMPEG'
        print(f"total_frames {render_frame_length}", flush=True)
        render.ffmpeg.format='MPEG4'
        render.ffmpeg.codec = "H264"
        render.ffmpeg.ffmpeg_preset='REALTIME'
        render.ffmpeg.constant_rate_factor='HIGH'
        render.ffmpeg.audio_codec='MP3'
        render.ffmpeg.gopsize = 30
        scene.display.shading.color_type = 'TEXTURE'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(animation=True)
        
    return main_filepath

def modify_npz(filename: str) -> str:
    # Load the .npz file
    data = np.load(filename)
    
    # Create a dictionary with the modified data
    new_data = {key: (np.zeros_like(data[key]) if key in ['expressions', 'trans'] else data[key]) for key in data}
    
    # Create a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_path = f"{temp_dir}/modified.npz"
    
    # Save the modified data
    np.savez(temp_path, **new_data)
    
    return temp_path

def compute_render_time(directory: str) ->str:
    
    renderTime = 0
    
    if directory is not str:
        directory = str(directory)
    
    files = [f for f in os.listdir(directory)]
    for file in files:
        # print(os.path.splitext(file)[0])
        SMPLX_TAKE = myPath(str(directory) + '/' + os.path.splitext(file)[0] + '.npz')
        file_arr = np.load(SMPLX_TAKE, allow_pickle=True)
        renderTime = renderTime + len(file_arr['poses'])
    
    return renderTime

def detect_files(directory: str) ->str:
    output_list = []
    
    if directory is not str:
        directory = str(directory)
    
    files = [f for f in os.listdir(directory)]
    
    if files is not None:
        for file in files:
            parts = file.replace(".mp4", "").split("_")
            result = "_".join(parts[1:-1])
            output_list.append(result)
            
    return output_list

def main(AUDIO_LOCATION_IN, SMPLX_TAKE_IN: myPath = None):
    start = time.time()
    
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
    elif not bpy.ops.text.run_script.poll():
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]
        
    ##################################
    ##### SET ARGUMENTS MANUALLY #####
    ##### IF RUNNING BLENDER GUI #####
    ##################################
    args = parser.parse_args()
    ARG_FRAMERATE = args['framerate'] if 'framerate' in args else 30
    ARG_MAIN_BVH_FILE = args['input_bvh'] if 'input_bvh' in args else ''
    ARG_MAIN_AUDIO_FILE = args['input_bvh_wav'].resolve() if 'input_bvh_wav' in args else ''
    ARG_IMAGE = args['png'] if 'png' in args else False
    ARG_VIDEO = args['video'] if 'video' in args else False
    ARG_START_FRAME = args['start'] if 'start' in args else [0]
    ARG_DURATION_IN_FRAMES = args['duration'] if 'duration' in args else [0]
    ARG_RESOLUTION_X = args['res_x'] if 'res_x' in args else 1440 #3840
    ARG_RESOLUTION_Y = args['res_y'] if 'res_y' in args else 1080 #2160
    ARG_MODE = args['visualization_mode'] if 'visualization_mode' in args else 'full_body'
    ARG_OUTPUT_DIR = args['output_dir'].resolve() if 'output_dir' in args else SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
    ARG_OUTPUT_NAME = args['output_name'] if 'output_name' in args else 'blender_output_1'
    
    assert "." not in str(ARG_OUTPUT_NAME), "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in str(ARG_OUTPUT_NAME) and "\\" not in str(ARG_OUTPUT_NAME), "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    print('ARG_OUTPUT_DIR: ', ARG_OUTPUT_DIR)
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
    
    # This is unused. Can be used to render everything missing from the output folder.
    output_dir_files = detect_files(ARG_OUTPUT_DIR)
    
    bpy.ops.object.smplx_add_animation(filepath=str(SMPLX_TAKE_IN))
    bpy.ops.object.select_all(action='DESELECT')
    edit_character.set_char_texture(SMPLX_TAKE_IN)
    
    # Select only armature
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            print("This is the selected armature: ", smplx_char)
            break
    
    smplx_char.select_set(True)
    bpy.ops.transform.rotate(value=-1.57, orient_axis='X')
    
    # Load hair and mask onto mesh
    edit_character.load_hair_and_mask(smplx_char, SCRIPT_DIR)
    
    # Normalize hips location to center of scene
    data = np.load(str(SMPLX_TAKE_IN), allow_pickle=True)
    trans = data['trans']  # Shape: (num_frames, 3)
    avg_pelvis_position = trans.mean(axis=0)
    smplx_char.pose.bones['root'].location[0] -= avg_pelvis_position[0]
    smplx_char.pose.bones['root'].location[1] -= avg_pelvis_position[2]
    smplx_char.pose.bones['root'].location[2] -= (avg_pelvis_position[1] - 1.3)
    
    output_name = smplx_char.name
    smplx_mesh = smplx_char.children[2]
    
    bpy.context.object.modifiers["Armature"].use_deform_preserve_volume = True
    
    # Add clothes to mesh
    create_material.setup_subdivision_surface(smplx_mesh)
    create_material.setup_material_nodes(smplx_mesh, SCRIPT_DIR)
    create_material.setup_geometry_nodes(smplx_mesh)
    
    # Audio
    load_data.load_audio(AUDIO_LOCATION_IN, SMPLX_TAKE_IN)
    
    # Camera
    MAIN_CAM_ROT = [1.57, 0, 0]
    CAM_POS = Vector((0, -2.45, 1.45))
    create_camera.add_camera(CAM_POS, MAIN_CAM_ROT, 'Main')
    
    for render_number in range(len(ARG_START_FRAME)):
        if ARG_DURATION_IN_FRAMES[render_number] == -1:
            main_fp = render_video(
                str(ARG_OUTPUT_DIR),
                ARG_FRAMERATE,
                ARG_IMAGE, 
                ARG_VIDEO, 
                output_name,
                ARG_START_FRAME[render_number],
                smplx_char.animation_data.action.frame_range.y, 
                ARG_RESOLUTION_X, 
                ARG_RESOLUTION_Y)
            continue
        
        main_fp = render_video(
                str(ARG_OUTPUT_DIR),
                ARG_FRAMERATE,
                ARG_IMAGE, 
                ARG_VIDEO, 
                output_name,
                ARG_START_FRAME[render_number],
                ARG_DURATION_IN_FRAMES[render_number], 
                ARG_RESOLUTION_X, 
                ARG_RESOLUTION_Y)
                
    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    print(all_time)

# START OF CODE
if bpy.ops.text.run_script.poll():
    SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]

file_path = 'S://Work//GENEA//GENEA2024//beat_v2.0.0//beat_english_v2.0.0//train_test_split.csv'
ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'

matches = load_data.filter_csv_by_type(file_path)
unique_names_list, unique_ids_list, unique_entry_list = load_data.extract_unique_names(matches)

all_start = time.time()

create_scene.clear_scene()

blend_file_path = os.path.join(SCRIPT_DIR, 'environments/IndoorEnvironment_smaller.blend')

with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
    data_to.objects = list(data_from.objects)  # Load all available objects

# Link the imported objects to the active collection
for obj in data_to.objects:
    if obj is not None:
        bpy.context.collection.objects.link(obj)

if bpy.ops.text.run_script.poll():
    print('[INFO] Script is running in Blender UI.')
    SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
    ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
    
    # TEAMS
    # SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/Team submissions/synthetic_baselines/attenuated/'
    SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/Team submissions/DiffuseStyleGesture/check/'
    AUDIO_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/wave16k/'
    
    # FILENAME TO LOAD
    SMPLX_FILENAME = '6_carla_0_65_65'
    
    # DATASET .NPZ
    SMPLX_LOCATION_DATASET = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/smplxflame_30/'
    SMPLX_FILENAME_DATASET = SMPLX_FILENAME
    SMPLX_FILENAME_DATASET = '6_carla_0_65_65'
    
    SMPLX_TAKE = load_data.check_files_npz(SMPLX_LOCATION, SMPLX_FILENAME, SMPLX_LOCATION_DATASET, SMPLX_FILENAME_DATASET)
    
    main(AUDIO_LOCATION, SMPLX_TAKE_IN=SMPLX_TAKE)
else:
    args = parser.parse_args()
    parser.check_args(args)
    
    ARG_NPZ_FILE = None
    ARG_NPZ_DIR = None
    ARG_NPZ_DATASET_LOCATION = None
    ARG_NPZ_DATASET_FILENAME = None
    
    ARG_NPZ_FILE = args['input_npz']
    ARG_NPZ_DIR = args['input_npz_dir']
    ARG_AUDIO_LOCATION = args['audo_wav']
    # ARG_NPZ_DATASET_LOCATION = args['input_npz_dataset_directory']
    # ARG_NPZ_DATASET_FILENAME = ARG_NPZ_FILE
    # ARG_NPZ_DATASET_FILENAME = args['input_npz_dataset_filename']
    
    if ARG_NPZ_FILE is not None and ARG_NPZ_DIR is not None:
        print('Please provide either a specific file or a directory of files. Not both at the same time!')
        exit()
    
    if ARG_NPZ_FILE is not None:
        ARG_NPZ_FILE = load_data.check_files_npz(ARG_NPZ_FILE.parent, ARG_NPZ_FILE.stem, ARG_NPZ_DATASET_LOCATION, ARG_NPZ_DATASET_FILENAME)
        print(ARG_NPZ_FILE)
        main(ARG_AUDIO_LOCATION, SMPLX_TAKE_IN=ARG_NPZ_FILE)
        create_scene.clear_character()
        
    if ARG_NPZ_DIR is not None:
        SMPLX_LOCATION = ARG_NPZ_DIR
        # SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/' + SMPLX_FILENAME_IN + '.npz')
        # print('write data to this one: ' + str(SMPLX_TAKE))
        
        if args['render_time'] is not False:
            renderTime = 0
            renderTime = compute_render_time(str(SMPLX_LOCATION))
            print(renderTime)
            print(float(renderTime/60/60/24))
            exit()
        
        files = [f for f in os.listdir(SMPLX_LOCATION)]
        i = 0
        
        for file in files:
            
            if not file.endswith(".npz"):
                continue
            
            # This needs to check for filename comparison and such
            ARG_NPZ_FILE = load_data.check_files_npz(SMPLX_LOCATION, os.path.splitext(file)[0], ARG_NPZ_DATASET_LOCATION, ARG_NPZ_DATASET_FILENAME)
            print(ARG_NPZ_FILE)
        
            main(ARG_AUDIO_LOCATION, SMPLX_TAKE_IN=ARG_NPZ_FILE)
            create_scene.clear_character()