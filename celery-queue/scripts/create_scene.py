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

def setup_scene(
    cam_pos,
    cam_rot,
    plane_size,
    InLocation):
    
    # Camera Main
    name = 'Main'
    create_camera.add_camera(cam_pos, cam_rot, name)
    
    add_plane(plane_size)
    
    light_type = 'AREA'
    add_light(InType=light_type, InRadius=5, InLightLocation=InLocation)

    # Sky Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=256, radius=75)
    sky_obj = bpy.data.objects['Sphere']
    sky_obj.name = 'Sky'
    
    sky_mat = bpy.data.materials.new(name="SkyBox")
    sky_mat.use_nodes = True
    bsdf = sky_mat.node_tree.nodes["Principled BSDF"]
    
    texImage = sky_mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture_dir = script_dir/"textures"/"beautiful-cloudy-sky.jpg"
    texImage.image = bpy.data.images.load(str(texture_dir))
    sky_mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    
    sky_obj.data.materials.append(sky_mat)
    
    sky_obj.rotation_euler[0] = 5.06145

def add_plane(prov_size):
    bpy.ops.mesh.primitive_plane_add(size=prov_size, location=[0, 0, 0])
    plane_obj = bpy.data.objects['Plane']
    plane_obj.name = 'Floor'
    plane_obj.scale[0] = 2.3
    plane_obj.scale[1] = 2.175
    plane_obj.rotation_euler[0] = -1.5708
    
    mat = bpy.data.materials.new(name="FloorColor") #create new material and variable
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture_dir = script_dir/"textures"/"grass-texture-background.jpg"
    texImage.image = bpy.data.images.load(str(texture_dir))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    
    plane_obj.data.materials.append(mat) #add the material to the object
    
    
    
def add_speechbubble(y):
    bpy.ops.mesh.primitive_uv_sphere_add()
    bub_obj = bpy.data.objects['Sphere']
    bub_obj.name = 'SpeechBubble'
    bub_obj.location[0] = 0
    bub_obj.location[1] = y
    bub_obj.location[2] = 1.85
    
    mat = bpy.data.materials.new(name="FloorColor") #create new material and variable
    mat.diffuse_color = (0.115, 0.25, 0.3, 1)
    bub_obj.data.materials.append(mat) #add the material to the object
    return bub_obj

def add_light(InType = 'SUN', InRadius = 1, InLightLocation = (0, 0, 0)):
    bpy.ops.object.light_add(type=InType, radius=InRadius)
    if InType == 'AREA':
        print('area added')
        sun_obj = bpy.data.objects['Area']
        sun_obj.data.energy = 30000
        sun_obj.data.size = 60.6
        sun_obj.rotation_euler[0] = 0.506145
    if InType == 'POINT':
        print('point added') 
        sun_obj = bpy.data.objects['Point']
        sun_obj.data.energy = 100
    sun_obj.location = InLightLocation
    print(sun_obj.location)