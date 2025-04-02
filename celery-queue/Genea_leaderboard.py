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
        
        matches = filter_csv_by_type(in_file_path)

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

def clear_character():
    bpy.ops.object.select_all(action='DESELECT')
    
    smplx_char = None
    
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            break
    
    if smplx_char is None:
        return
    
    children = [child for child in smplx_char.children if child.type == 'MESH']
    for mesh_obj in children:
        # Step 2: Remove Materials from Mesh
        if mesh_obj.data.materials:
            for mat in mesh_obj.data.materials:
                if mat:
                    bpy.data.materials.remove(mat, do_unlink=True)
        
        # Step 3: Unlink and delete the mesh object
        bpy.data.objects.remove(mesh_obj, do_unlink=True)

    # Step 4: Delete animation data if any
    if smplx_char.animation_data and smplx_char.animation_data.action:
        action = smplx_char.animation_data.action
        smplx_char.animation_data_clear()
        bpy.data.actions.remove(action, do_unlink=True)

    # Step 5: Remove the Armature
    bpy.data.objects.remove(smplx_char, do_unlink=True)
    
    for sound in bpy.data.sounds:
        bpy.data.sounds.remove(sound, do_unlink=True)
    
    for obj_cam in bpy.data.objects:
        if obj_cam.type == 'CAMERA':
            cam = obj_cam
            break
    
    bpy.data.objects.remove(cam, do_unlink=True)
    
    # bpy.ops.ed.undo_push(message="Cleanup")
    # bpy.ops.ed.undo()
    
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    # gc.collect()

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

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_npz', help='Input filename of the NPZ file.', type=myPath, required=True)
    parser.add_argument('-imb', '--input_main_bvh', help='Input filename of the main agent BVH motion file.', type=myPath)
    parser.add_argument('-iib', '--input_intr_bvh', help='Input filename of the interlocutor BVH motion file', type=myPath)
    parser.add_argument('-imw', '--input_main_wav', help='Input filename of the main agent WAV audio file.', type=myPath)
    parser.add_argument('-iiw', '--input_intr_wav', help='Input filename of the interlocutor WAV audio file.', type=myPath)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=myPath)
    parser.add_argument('-n', '--output_name', help='The name to use when outputting intermediate and final files. No periods \".\" or slashes \"/\" / \"\\\" allowed.', type=str, required=True)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=30)
    parser.add_argument('-p', '--png', action='store_true', help='Renders the result in a PNG-formatted image.')
    parser.add_argument('-v', '--video', action='store_true', help='Renders the result in an MP4-formatted video.')
    parser.add_argument('-m', "--visualization_mode", help='The visualization mode to use for rendering.',type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', help='The horizontal resolution for the rendered videos.', type=int, default=1440)
    parser.add_argument('-ry', '--res_y', help='The vertical resolution for the rendered videos.', type=int, default=1080)
    parser.add_argument('-f', '--framerate', help='The requested framerate.', type=int, default=30)
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

def main(SMPLX_FILENAME_IN = ""):
    start = time.time()
    
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
        ARG_NPZ_FILE = None
        ARG_FRAMERATE = 30
        ARG_MAIN_BVH_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/internal/main-agent/bvh/tst_2023_v0_024_main-agent.bvh'
        ARG_MAIN_AUDIO_FILE = 'S:/Work/GENEA2022/genea2023_dataset_tst/tst/main-agent/wav_norm/tst_2023_v0_024_main-agent.wav' # set to None for no audio
        ARG_IMAGE = False
        ARG_VIDEO = True
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 30
        ARG_RESOLUTION_X = 1440 #3840
        ARG_RESOLUTION_Y = 1080 #2160
        ARG_MODE = 'full_body'
        ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        ARG_OUTPUT_NAME = 'blender_output_1'
        
        ARG_PLANESIZE = 10
        ARG_LIGHTLOCATION = [0, 5, 15]
        print('ARG_OUTPUT_DIR: ', ARG_OUTPUT_DIR)
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]
        args = parse_args()
        ARG_NPZ_FILE = args['input_npz']
        ARG_FRAMERATE = args['framerate']
        ARG_MAIN_BVH_FILE = args['input_main_bvh']
        ARG_MAIN_AUDIO_FILE = args['input_main_wav'].resolve() if args['input_main_wav'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video']
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else SCRIPT_DIR / 'output/'
        ARG_OUTPUT_NAME = args['output_name']
        
        ARG_PLANESIZE = 10
        ARG_LIGHTLOCATION = [0, 5, 15]
    
    output_dir = ARG_OUTPUT_DIR
    
    if not os.path.exists(str(output_dir)):
        os.mkdir(str(output_dir))
    
    output_name = ARG_OUTPUT_NAME
    assert "." not in output_name, "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in output_name and "\\" not in output_name, "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    bpy.ops.object.select_all(action='DESELECT')
    SMPLX_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/smplxflame_30/'
    SMPLX_TAKE = myPath(SMPLX_LOCATION + SMPLX_FILENAME_IN + '.npz')
    
    if ARG_NPZ_FILE is not None:
        SMPLX_TAKE = ARG_NPZ_FILE
        
    char_name_mid = re.search(r'(\d+_[a-zA-Z]+)', SMPLX_TAKE.stem)
    char_name = re.match(r"(\d+)_([a-zA-Z]+)", char_name_mid.group(1))

    texture_type = 'male'

    if char_name.group(2) in female_names:
        texture_type = 'female'
    
    # NEW_SMPLX_PATH = modify_npz(SMPLX_TAKE)
    
    bpy.ops.object.smplx_add_animation(filepath=str(SMPLX_TAKE))
    
    # bpy.ops.object.smplx_reset_expression_shape()
    # bpy.ops.object.smplx_reset_poseshapes()
    
    bpy.ops.object.select_all(action='DESELECT')
    
    if texture_type == 'female':
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_m_alb.png'
    else:
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
        
    bpy.ops.object.smplx_set_texture()
    
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            break
        
    # Add hair and mask
    hair_blend_file_path = os.path.join(SCRIPT_DIR, 'environments/smplx_genea_male.blend')
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

    root_bone = smplx_char.pose.bones['root']
    pelvis_bone = smplx_char.pose.bones['pelvis']
    
    # ARG_DURATION_IN_FRAMES = smplx_char.animation_data.action.frame_range.y
    output_name = smplx_char.name
    
    smplx_mesh = smplx_char.children[0]
    
    create_material.setup_subdivision_surface(smplx_mesh)
    create_material.setup_material_nodes(smplx_mesh, script_dir)
    create_material.setup_geometry_nodes(smplx_mesh)
    
    AUDIO_LOCATION = 'S:/Work/GENEA/GENEA2024/beat_v2.0.0/beat_english_v2.0.0/wave16k/'
    ARG_MAIN_AUDIO_FILE = AUDIO_LOCATION + SMPLX_FILENAME_IN + '.wav' # set to None for no audio
    
    create_sequencer()
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
        
    main_fp = render_video(
        str(output_dir), 
        ARG_FRAMERATE,
        ARG_IMAGE, 
        ARG_VIDEO, 
        output_name + str(ARG_RESOLUTION_Y),
        ARG_START_FRAME, 
        ARG_DURATION_IN_FRAMES, 
        ARG_RESOLUTION_X, 
        ARG_RESOLUTION_Y)
        
    end = time.time()
    all_time = end - start
    print("output_file", str(list(output_dir.glob("*"))[0]), flush=True)
    print(all_time)

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

def extract_unique_names(file_path):
    unique_names = {}
    unique_ids = {}
    unique_list = {}
    
    # with open(file_path, "r") as file:
    for line in file_path:
        # Search for names in the pattern: number_name
        match = re.search(r'(\d+_[a-zA-Z]+)', line)
        if match:
            idname = match.group(1)
            
            match2 = re.match(r"(\d+)_([a-zA-Z]+)", idname)
            id = match2.group(1)
            name = match2.group(2)
            
            # Check if "test" is in the same line (assuming it's in the next column)
            if name not in unique_names:
                unique_names[name] = line.strip() 
                unique_ids[id] = line.strip() # Store the full matching line if needed
                unique_list[idname] = line.strip()

    return list(unique_names.keys()), list(unique_ids.keys()), list(unique_list.values())

if bpy.ops.text.run_script.poll():
    SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    SCRIPT_DIR = myPath(os.path.realpath(__file__)).parents[0]

file_path = 'S://Work//GENEA//GENEA2024//beat_v2.0.0//beat_english_v2.0.0//train_test_split.csv'
ARG_OUTPUT_DIR = SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'

female_names = ['kieks', 'ayana', 'luqi', 'hailing', 'kexin', 'goto', 'yingqing', 'tiffnay', 'katya', 'carla', 'sophie', 'miranda']
male_names = ['wayne', 'nidal', 'zhao', 'lu', 'carlos', 'jorge', 'itoi', 'daiki', 'li', 'scott', 'solomon', 'lawrence', 'stewart']

matches = filter_csv_by_type(file_path)
unique_names_list, unique_ids_list, unique_entry_list = extract_unique_names(matches)

all_start = time.time()

clear_scene()

blend_file_path = os.path.join(SCRIPT_DIR, 'environments/IndoorEnvironment_smaller.blend')

with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
    data_to.objects = list(data_from.objects)  # Load all available objects

# Link the imported objects to the active collection
for obj in data_to.objects:
    if obj is not None:
        bpy.context.collection.objects.link(obj)

# bpy.utils.register_class(SequentialRenderOperator)
# bpy.ops.render.sequential_animations()

# for File in unique_entry_list:
#     print(File)
#     char_name_mid = re.search(r'(\d+_[a-zA-Z]+)', File)
#     char_name = re.match(r"(\d+)_([a-zA-Z]+)", char_name_mid.group(1))
    
#     texture_type = 'male'
    
#     if char_name.group(2) in female_names:
#         texture_type = 'female'
    
#     SMPLX_FILENAME_IN = File
#     main(SMPLX_FILENAME_IN)
#     clear_character()
    
#     for Output_File in list(ARG_OUTPUT_DIR.glob("*")):
#         print(Output_File)
#         segment = extract_segment(str(Output_File))
#         if segment in File:
# #           print("Extracted segment:", segment)
#             print(Output_File.stem)
#             main(SMPLX_FILENAME_IN)
#             clear_character()
    
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
clear_character()