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
import gc
import tempfile

class SequentialRenderOperator(bpy.types.Operator):
    bl_idname = "render.sequential_animations"
    bl_label = "Render Animations Sequentially"
    
    render_queue = []
    is_rendering = False
    
    def execute(self, context):
        # Define the animations (scenes or cameras to render)
        self.render_queue = self.setup_queue()
        
        # self.render_queue = [
        #     {"filepath": "//output/animation1_", "start": 1, "end": 100},
        #     {"filepath": "//output/animation2_", "start": 101, "end": 200},
        # ]
        
        # Start the modal handler
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
    
    def modal(self, context, event):
        if not self.is_rendering:
            if self.render_queue:
                
                clear_character()
                
                render_settings = self.render_queue.pop(0)
                SMPLX_FILENAME_IN = render_settings["filepath"]
                main() # Should have the take path as parameter for main(SMPLX_FILENAME_IN)
                
                # Start rendering
                self.is_rendering = True
                bpy.ops.render.render('EXEC_DEFAULT', animation=True)
            else:
                # No more renders left, finish operator
                return {"FINISHED"}
        
        # Check if rendering is done
        if not bpy.app.is_job_running("RENDER"):
            self.is_rendering = False  # Ready for next render

        return {"RUNNING_MODAL"}
    
    def setup_queue(self):
        render_queue = []
        
        IN_SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
        in_file_path = 'S://Work//GENEA//GENEA2024//beat_v2.0.0//beat_english_v2.0.0//train_test_split.csv'
        IN_ARG_OUTPUT_DIR = IN_SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        
        matches = load_data.filter_csv_by_type(in_file_path)

        i = 0
        for File in matches:
            if (i == 85): # was 87
                print(File)
                render_queue.append({
                    "filepath": File,
                })
                
            if (i == 126):
                print(File)
                render_queue.append({
                    "filepath": File,
                })
            
            i += 1
            
        return render_queue

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
import parser
importlib.reload(parser)
    
def setup_char_clothes(char):
    mesh = char.children[0]
    mat = mesh.material_slots[0].material
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    bsdf_node = mat.node_tree.nodes["Principled BSDF"]
    material_output = mat.node_tree.nodes["Material Output"]
    
    for node in nodes:
        if node.type == 'TEX_IMAGE':
            texture_diffuse = node
    
    texture_displacement = nodes.new(type='ShaderNodeTexImage')
    multiply_node = nodes.new(type='ShaderNodeVectorMath')
    multiply_node.operation = 'MULTIPLY'
    scale_node = nodes.new(type='ShaderNodeVectorMath')
    scale_node.operation = 'SCALE'
    attribute_node = nodes.new(type='ShaderNodeAttribute')
    value_node = nodes.new(type='ShaderNodeValue')
    divide_node = nodes.new(type='ShaderNodeMath')
    divide_node.operation = 'DIVIDE'

    # Position the nodes
    texture_diffuse.location      = (-600, 200)
    texture_displacement.location = (-600, -100)
    attribute_node.location       = (-600, -400)
    value_node.location           = (-400, -500)
    bsdf_node.location                 = (-200, 200)
    multiply_node.location        = (-200, -200)
    divide_node.location          = (-200, -400)
    scale_node.location           = (0, -200)
    material_output.location            = (200, -200)
    
    try:
        diffuse_filepath = texture_diffuse.image.filepath
        if "smplx_texture_f_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_f_disp.png"
        elif "smplx_texture_m_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_m_disp.png"
        else:
            print(f"Could not determine displacement texture from filepath: {diffuse_filepath}")
            return

        if texture_filename not in bpy.data.images:
            print(os.path.realpath(__file__))
            addon_path = os.path.dirname(os.path.realpath(__file__))
            texture_path = os.path.join(addon_path, "data", texture_filename)
            texture_displacement.image = bpy.data.images.load(texture_path)
        else:
            texture_displacement.image = bpy.data.images[texture_filename]

    except RuntimeError:
        print(f"Failed to load texture: {texture_path}")
        return

    attribute_node.attribute_name = "norm"
    value_node.outputs['Value'].default_value = 10
    divide_node.inputs[1].default_value = 1000

    # Create connections
    links.new(texture_diffuse.outputs['Color'], bsdf_node.inputs['Base Color'])
    links.new(bsdf_node.outputs['BSDF'], material_output.inputs['Surface'])
    links.new(texture_displacement.outputs['Color'], multiply_node.inputs[0])
    links.new(attribute_node.outputs['Vector'], multiply_node.inputs[1])
    links.new(multiply_node.outputs['Vector'], scale_node.inputs['Vector'])
    links.new(value_node.outputs['Value'], divide_node.inputs[0])
    links.new(divide_node.outputs['Value'], scale_node.inputs['Scale'])
    links.new(scale_node.outputs['Vector'], material_output.inputs['Displacement'])
    
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
    config = {}
    
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
        ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        
        config = parser.load_json_config(SCRIPT_DIR)
        
        if len(config) == 0:
            print('No config found! Blender UI will use some default values!')
        
    ##################################
    ##### SET ARGUMENTS MANUALLY #####
    ##### IF RUNNING BLENDER GUI #####
    ##################################
    ARG_FRAMERATE = config.get('framerate') if 'framerate' in config else 30
    ARG_MAIN_BVH_FILE = ''
    ARG_MAIN_AUDIO_FILE = ''
    ARG_IMAGE = config.get('png') if 'png' in config else False
    ARG_VIDEO = config.get('video') if 'video' in config else False
    ARG_START_FRAME = config.get('start') if 'start' in config else 0
    ARG_DURATION_IN_FRAMES = config.get('duration') if 'duration' in config else 0
    ARG_RESOLUTION_X = config.get('res_x') if 'res_x' in config else 1440 #3840
    ARG_RESOLUTION_Y = config.get('res_y') if 'res_y' in config else 1080 #2160
    ARG_MODE = config.get('visualization_mode') if 'visualization_mode' in config else 'full_body'
    ARG_OUTPUT_NAME = config.get('output_name') if 'output_name' in config else 'blender_output_1'
    
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

    pelvis_bone = smplx_char.pose.bones['pelvis']
    output_name = smplx_char.name
    smplx_mesh = smplx_char.children[0]
    
    bpy.context.object.modifiers["Armature"].use_deform_preserve_volume = True
    
    create_material.setup_subdivision_surface(smplx_mesh)
    create_material.setup_material_nodes(smplx_mesh, script_dir)
    create_material.setup_geometry_nodes(smplx_mesh)
    
    ARG_MAIN_AUDIO_FILE = AUDIO_LOCATION_IN + SMPLX_TAKE_IN.stem + '.wav' # set to None for no audio
    
    bpy.context.scene.sequence_editor_create()
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    try:
        ARG_MAIN_AUDIO_FILE
    except:
        ARG_MAIN_AUDIO_FILE = ''
    
    if ARG_MAIN_AUDIO_FILE and not IS_SERVER:
        load_data.load_audio(str(ARG_MAIN_AUDIO_FILE), 1)
            
    MAIN_CAM_ROT = [0, 0, 0]
    CAM_POS = Vector((
        pelvis_bone.location[0], 
        pelvis_bone.location[1], 
        pelvis_bone.location[2])) + Vector((0, -0.375, 4))
    
    create_scene.setup_scene(
        CAM_POS,
        MAIN_CAM_ROT,
        ARG_PLANESIZE,
        ARG_LIGHTLOCATION)

    bpy.ops.object.select_all(action='DESELECT')
    
    smplx_char.select_set(True)
    mainCam = bpy.data.objects['Main_cam']
    mainCam.select_set(True)
    
    bpy.ops.transform.rotate(value=-1.57, orient_axis='X')
    
    mainCam.location[1] += 1.875
    mainCam.location[2] += 0.4
    
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

# bpy.utils.register_class(SequentialRenderOperator)
# bpy.ops.render.sequential_animations()

# DiffuseStyleGesture
# SG_DIR = 'S://Work//GENEA//GENEA2024//Team submissions//The_Semantic_Gesticulator//data1//zhangzeyi//SG_results_for_GENEA//save_res_all_only_bvh_with_root_height//'


if bpy.ops.text.run_script.poll():
    print('[INFO] Script is running in Blender UI.')
    SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
    ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
    
    # TEAMS
    # SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/Team submissions/The_Semantic_Gesticulator/check/'
    SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/Team submissions/DiffuseStyleGesture/check/'
    AUDIO_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/wave16k/'
    
    # FILENAME TO LOAD
    SMPLX_FILENAME = '22_luqi_0_2_2'
    
    # DATASET .NPZ
    SMPLX_LOCATION_DATASET = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/smplxflame_30/'
    SMPLX_FILENAME_DATASET = SMPLX_FILENAME
    SMPLX_FILENAME_DATASET = '22_luqi_0_2_2'
    
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