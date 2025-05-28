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
    
    if directory is not str:
        directory = str(directory)
    
    files = [f for f in os.listdir(directory)]
    return files

def set_char_texture(SMPLX_TAKE):
    if SMPLX_TAKE is None:
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
        return
    
    # File format must start with 1_name_0_#_#_... .npz, otherise this will fail
    char_name_mid = re.search(r'(\d+_[a-zA-Z]+)', SMPLX_TAKE.stem)
    char_name = re.match(r"(\d+)_([a-zA-Z]+)", char_name_mid.group(1))
    
    print(char_name_mid)
    print(char_name)
    
    female_names = ['kieks', 'ayana', 'luqi', 'hailing', 'kexin', 'goto', 'yingqing', 'tiffnay', 'katya', 'carla', 'sophie', 'miranda']
    male_names = ['wayne', 'nidal', 'zhao', 'lu', 'carlos', 'jorge', 'itoi', 'daiki', 'li', 'scott', 'solomon', 'lawrence', 'stewart']
    
    texture_type = 'male'
    if char_name.group(2) in female_names:
        texture_type = 'female'
        print(texture_type)
    
    if texture_type == 'female':
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_m_alb.png'
    else:
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
        
    bpy.ops.object.smplx_set_texture()

def main(AUDIO_LOCATION_IN, SMPLX_TAKE_IN: myPath = None):
    start = time.time()
    
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
        ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        
    ##################################
    ##### SET ARGUMENTS MANUALLY #####
    ##### IF RUNNING BLENDER GUI #####
    ##################################
    ARG_FRAMERATE = 30
    ARG_MAIN_BVH_FILE = ''
    ARG_MAIN_AUDIO_FILE = ''
    ARG_IMAGE = False
    ARG_VIDEO = False
    ARG_START_FRAME = 0
    ARG_DURATION_IN_FRAMES = 0
    ARG_RESOLUTION_X = 1440 #3840
    ARG_RESOLUTION_Y = 1080 #2160
    ARG_MODE = 'full_body'
    ARG_OUTPUT_NAME = 'blender_output_1'
    
    ARG_PLANESIZE = 10
    ARG_LIGHTLOCATION = [0, 5, 15]

    if not bpy.ops.text.run_script.poll():
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]
        args = parser.parse_args()
        ARG_FRAMERATE = args['framerate']
        ARG_MAIN_BVH_FILE = args['input_bvh']
        ARG_MAIN_AUDIO_FILE = args['input_bvh_wav'].resolve() if args['input_bvh_wav'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video']
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else SCRIPT_DIR / 'output/'
        ARG_OUTPUT_NAME = args['output_name']
    
    assert "." not in str(ARG_OUTPUT_NAME), "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in str(ARG_OUTPUT_NAME) and "\\" not in str(ARG_OUTPUT_NAME), "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    print('ARG_OUTPUT_DIR: ', ARG_OUTPUT_DIR)
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
    
    output_dir_files = detect_files(ARG_OUTPUT_DIR)
    output_dir_files_short = []
    
    if output_dir_files is not None:
        for file in output_dir_files:
            parts = file.replace(".mp4", "").split("_")
            result = "_".join(parts[1:-1])
            output_dir_files_short.append(result)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.smplx_add_animation(filepath=str(SMPLX_TAKE_IN))
    # bpy.ops.object.smplx_reset_expression_shape()
    # bpy.ops.object.smplx_reset_poseshapes()
    bpy.ops.object.select_all(action='DESELECT')
    
    set_char_texture(SMPLX_TAKE_IN)
    
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            break
        
    # Add hair and mask
    hair_blend_file_path = os.path.join(SCRIPT_DIR, 'environments/smplx_genea_male_simplified.blend')
    meshes_to_import = ["mask_male", "male_hair"]  # Replace with actual names

    if os.path.isfile(hair_blend_file_path):
        with bpy.data.libraries.load(hair_blend_file_path, link=False) as (data_from, data_to):
            data_to.objects = [mesh for mesh in data_from.objects if mesh in meshes_to_import]  # Load all available objects
            print(list(data_from.objects))
            print(data_to.objects)
            
        # Link the imported objects to the active collection
        for obj in data_to.objects:
            if obj is not None:
                print(obj)
                obj.rotation_euler[0] -= 1.64
                obj.location = (-0.0125, -0.075, 0.0925)
                bpy.context.collection.objects.link(obj)
                obj.parent = smplx_char
                obj.parent_type = "BONE"
                obj.parent_bone = "head"
                
        obj.location = (-0.005, -0.03, -0.05)
    
    data = np.load(str(SMPLX_TAKE_IN), allow_pickle=True)
    trans = data['trans']  # Shape: (num_frames, 3)
    print(trans)
    avg_pelvis_position = trans.mean(axis=0)
    smplx_char.pose.bones['root'].location[0] -= avg_pelvis_position[0]
    smplx_char.pose.bones['root'].location[1] -= avg_pelvis_position[2]
    smplx_char.pose.bones['root'].location[2] -= (avg_pelvis_position[1] - 1.3)
    
    output_name = smplx_char.name
    smplx_mesh = smplx_char.children[2]
    
    bpy.context.object.modifiers["Armature"].use_deform_preserve_volume = True
    
    create_material.setup_subdivision_surface(smplx_mesh)
    create_material.setup_material_nodes(smplx_mesh, SCRIPT_DIR)
    create_material.setup_geometry_nodes(smplx_mesh)
    
    # this changes 2_scott_0_1_1_sample_1 -> 2_scott_0_1_1
    # wav_name = SMPLX_TAKE_IN.stem.rsplit('_sample_', 1)[0]
    # ARG_MAIN_AUDIO_FILE = myPath(str(AUDIO_LOCATION_IN) + '/' + str(wav_name) + '.wav') # set to None for no audio
    ARG_MAIN_AUDIO_FILE = myPath(str(AUDIO_LOCATION_IN) + '/' + str(SMPLX_TAKE_IN.stem) + '.wav') # set to None for no audio
    print(ARG_MAIN_AUDIO_FILE)
    
    bpy.context.scene.sequence_editor_create()
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    try:
        ARG_MAIN_AUDIO_FILE
    except:
        ARG_MAIN_AUDIO_FILE = ''
        
    assert ARG_MAIN_AUDIO_FILE.is_file()
    
    if ARG_MAIN_AUDIO_FILE and not IS_SERVER:
        load_data.load_audio(str(ARG_MAIN_AUDIO_FILE), 1)
    
    MAIN_CAM_ROT = [1.57, 0, 0]
    CAM_POS = Vector((0, -2.45, 1.45))
    
    create_scene.setup_scene(
        CAM_POS,
        MAIN_CAM_ROT,
        ARG_PLANESIZE,
        ARG_LIGHTLOCATION)

    bpy.ops.object.select_all(action='DESELECT')
    
    smplx_char.select_set(True)
    
    bpy.ops.transform.rotate(value=-1.57, orient_axis='X')
    
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