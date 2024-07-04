import bpy
from pathlib import Path as myPath
import importlib
import os

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]

import edit_character
importlib.reload(edit_character)

def load_audio(filepath, name):
    bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip' + str(name),
        filepath=filepath,
        channel=name,
        frame_start=0
    )
    
def load_fbx(filepath, name):
    print(script_dir)
    bpy.ops.import_scene.fbx(
        filepath=filepath, 
        ignore_leaf_bones=True, 
        force_connect_children=True, 
        automatic_bone_orientation=False
    )
    edit_character.remove_bone(
        bpy.data.objects['Armature'], 
        'b_r_foot_End'
    )
    bpy.data.objects['Armature'].name = name
        
def load_bvh(filepath):
    bpy.ops.import_anim.bvh(
        filepath=filepath, 
        use_fps_scale=False,
        update_scene_fps=False, 
        update_scene_duration=True, 
        global_scale=0.01
    )