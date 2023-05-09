import bpy
import math
import os
from pathlib import Path as myPath
import importlib

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]

import create_camera
importlib.reload(create_camera)

def setup_scene(cam_pos, cam_rot, actor1, actor2, arm1, arm2, plane_size=5):
    
    # Camera Main
    name = 'Main'
    create_camera.add_camera(cam_pos, cam_rot, name)
    
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
    create_camera.add_camera(cam_pos, cam_rot, actor2.name)
    
    cam_pos = [0, -0.75, 1.5]
    cam_rot = [math.radians(80), 0, 0]
    create_camera.add_camera(cam_pos, cam_rot, actor1.name)
    
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