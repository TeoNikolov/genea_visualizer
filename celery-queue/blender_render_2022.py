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

# cleans up the scene and memory
def clear_scene():
    for block in bpy.data.meshes:   	bpy.data.meshes.remove(block)
    for block in bpy.data.materials:	bpy.data.materials.remove(block)
    for block in bpy.data.textures: 	bpy.data.textures.remove(block)
    for block in bpy.data.images:   	bpy.data.images.remove(block)  
    for block in bpy.data.curves:   	bpy.data.curves.remove(block)
    for block in bpy.data.cameras:  	bpy.data.cameras.remove(block)
    for block in bpy.data.lights:   	bpy.data.lights.remove(block)
    for block in bpy.data.sounds:   	bpy.data.sounds.remove(block)
    for block in bpy.data.armatures:	bpy.data.armatures.remove(block)
    for block in bpy.data.objects:  	bpy.data.objects.remove(block)
    for block in bpy.data.actions:  	bpy.data.actions.remove(block)
            
    if bpy.context.object == None:  		bpy.ops.object.delete()
    elif bpy.context.object.mode == 'EDIT': bpy.ops.object.mode_set(mode='OBJECT')
    elif bpy.context.object.mode == 'POSE': bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
    
def setup_scene(cam_pos, cam_rot):
    # Camera
    bpy.ops.object.camera_add(enter_editmode=False, location=cam_pos, rotation=cam_rot)
    cam = bpy.data.objects['Camera']
    cam.scale = [20, 20, 20]
    bpy.context.scene.camera = cam # add cam so it's rendered
    
    # Floor Plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=[0, 0, 0], rotation=[0, 0, 0])
    plane_obj = bpy.data.objects['Plane']
    plane_obj.name = 'Floor'
    plane_obj.scale = [100, 100, 100]
    mat = bpy.data.materials['FloorColor'] #set new material to variable
    plane_obj.data.materials.append(mat) #add the material to the object
    
    # Back Wall
    bpy.ops.mesh.primitive_plane_add(size=20, location=[0, 1, 0], rotation=[0, math.radians(90), math.radians(90)])
    plane1_obj = bpy.data.objects['Plane']
    plane1_obj.name = 'Wall_Back'
    plane1_obj.scale = [100, 100, 100]
    plane1_obj.data.materials.append(mat) #add the material to the object

def remove_bone(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones: # deselect the other bones
        if bone.name == bone_name:
            armature.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_fbx(fbx_path):
    bpy.ops.import_scene.fbx(filepath=fbx_path, ignore_leaf_bones=True, 
    force_connect_children=True, automatic_bone_orientation=False)
    remove_bone(bpy.data.objects['Armature'], 'b_r_foot_End')
        
def load_bvh(filepath, turn, zerofy=False):
    print("Turn flag: ", turn)
    if turn == 'default':
        bpy.ops.import_anim.bvh(filepath=filepath, axis_forward="-Z", use_fps_scale=False,
        update_scene_fps=True, update_scene_duration=True, global_scale=0.01)
    elif turn == 'ccw':
        bpy.ops.import_anim.bvh(filepath=filepath, axis_forward="-X", use_fps_scale=False,
        update_scene_fps=True, update_scene_duration=True, global_scale=0.01)
    elif turn == 'cw':
        bpy.ops.import_anim.bvh(filepath=filepath, axis_forward="X", use_fps_scale=False,
        update_scene_fps=True, update_scene_duration=True, global_scale=0.01)
    elif turn == 'flip':
        bpy.ops.import_anim.bvh(filepath=filepath, axis_forward="Z", use_fps_scale=False,
        update_scene_fps=True, update_scene_duration=True, global_scale=0.01)
    else:
        raise NotImplementedError('Turn flag "{}" is not implemented.'.format(turn))
        
    if zerofy:
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bone_pose = bpy.context.selected_pose_bones[0]
        bpy.ops.pose.select_all(action='DESELECT')
        bone_pose.bone.select = True
        if bone_pose.location.to_tuple(2) == (0.0, 0.0, 0.0):
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='SELECT')
            bone = bpy.context.selected_editable_bones[0]
            bpy.ops.armature.select_all(action='DESELECT')
            bone.select_head = True
            bpy.context.scene.cursor.location = bone.head
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.context.object.location = [0, 0, 0]
            bpy.context.scene.cursor.location = [0, 0, 0]

def add_materials(work_dir):
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
    
def load_audio(filepath):
    bpy.context.scene.sequence_editor_create()
    bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip',
        filepath=filepath,
        channel=1,
        frame_start=0
    )
    
def render_video(output_dir, picture, video, bvh_fname, render_frame_start, render_frame_length, res_x, res_y):
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
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}.png'.format(bvh_fname))
        bpy.ops.render.render(write_still=True)
        
    if video:
        print(f"total_frames {render_frame_length}", flush=True)
        bpy.context.scene.render.image_settings.file_format='FFMPEG'
        bpy.context.scene.render.ffmpeg.format='MPEG4'
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.ffmpeg_preset='REALTIME'
        bpy.context.scene.render.ffmpeg.constant_rate_factor='HIGH'
        bpy.context.scene.render.ffmpeg.audio_codec='MP3'
        bpy.context.scene.render.ffmpeg.gopsize = 30
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_'.format(bvh_fname))
        bpy.ops.render.render(animation=True, write_still=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', help='Input file name of the BVH to render.', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-r', '--rotate', help='Rotates the character for better positioning in the video frame. Use "cw" for 90-degree clockwise, "ccw" for 90-degree counter-clockwise, "flip" for 180 degree rotation, or leave at "default" for no rotation.', choices=['default', 'cw', 'ccw', 'flip'], type=str, default="default")
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600)
    parser.add_argument('-a', '--input_audio', help='Input file name of an audio clip to include in the final render.', type=Path)
    parser.add_argument('-p', '--png', action='store_true', help='Renders the result in a PNG-formatted image.')
    parser.add_argument('-v', '--video', action='store_true', help='Renders the result in an MP4-formatted video.')
    parser.add_argument('-m', "--visualization_mode", help='The visualization mode to use for rendering.',type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', help='The horizontal resolution for the rendered videos.', type=int, default=1024)
    parser.add_argument('-ry', '--res_y', help='The vertical resolution for the rendered videos.', type=int, default=768)  
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

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
        ARG_BVH_PATHNAME = SCRIPT_DIR / 'session30_take5_hasFingers_shallow26_scale_local_30fps_3k.bvh'
        ARG_AUDIO_FILE_NAME = SCRIPT_DIR / 'take5_shallow26.wav' # set to None for no audio
        ARG_IMAGE = False
        ARG_VIDEO = True
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 3600
        ARG_ROTATE = 'default'
        ARG_RESOLUTION_X = 1024
        ARG_RESOLUTION_Y = 768
        ARG_MODE = 'full_body'
        ARG_OUTPUT_DIR = ARG_BVH_PATHNAME.parents[0]
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = Path(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        ARG_BVH_PATHNAME = args['input']
        ARG_AUDIO_FILE_NAME = args['input_audio'].resolve() if args['input_audio'] else None
        ARG_IMAGE = args['png']
        ARG_VIDEO = args['video'] # set to 'False' to get a quick image preview
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_ROTATE = args['rotate']
        ARG_RESOLUTION_X = args['res_x']
        ARG_RESOLUTION_Y = args['res_y']
        ARG_MODE = args['visualization_mode']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else ARG_BVH_PATHNAME.parents[0]
        
        
    if ARG_MODE not in ["full_body", "upper_body"]:
        raise NotImplementedError("This visualization mode is not supported ({})!".format(ARG_MODE))
    
    # FBX file
    FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "GenevaModel_v2_Tpose_Final.fbx")
    BVH_NAME = os.path.basename(ARG_BVH_PATHNAME).replace('.bvh','')

    start = time.time()
    
    clear_scene()
    load_fbx(FBX_MODEL)
    add_materials(SCRIPT_DIR)
    load_bvh(str(ARG_BVH_PATHNAME), ARG_ROTATE, zerofy=True)
    constraintBoneTargets(rig = BVH_NAME, mode = ARG_MODE)

    if ARG_MODE == "full_body": 	CAM_POS = [0, -3, 1.1]
    elif ARG_MODE == "upper_body":  CAM_POS = [0, -2.45, 1.3]
    CAM_ROT = [math.radians(90), 0, 0]
    setup_scene(CAM_POS, CAM_ROT)
    
    # for sanity, audio is handled using FFMPEG on the server and the input_audio argument should be ignored
    if ARG_AUDIO_FILE_NAME and not IS_SERVER:
        load_audio(str(ARG_AUDIO_FILE_NAME))
    
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
        
    total_frames = bpy.data.objects[BVH_NAME].animation_data.action.frame_range.y
    render_video(str(ARG_OUTPUT_DIR), ARG_IMAGE, ARG_VIDEO, BVH_NAME, ARG_START_FRAME, min(ARG_DURATION_IN_FRAMES, total_frames), ARG_RESOLUTION_X, ARG_RESOLUTION_Y)

    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    
#Code line
main()