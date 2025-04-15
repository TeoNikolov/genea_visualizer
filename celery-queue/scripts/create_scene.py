import bpy
import math
import os
from pathlib import Path as myPath
import importlib
import random

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]

import create_camera
importlib.reload(create_camera)

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

def setup_scene(
    cam_pos,
    cam_rot,
    plane_size,
    InLocation):
    
    # Camera Main
    name = 'Main'
    create_camera.add_camera(cam_pos, cam_rot, name)
    
    # add_plane(plane_size)
    
#    light_type = 'AREA'
#    add_light(InType=light_type, InRadius=5, InLightLocation=InLocation)

    # Sky Sphere
    # bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=256, radius=75)
    # sky_obj = bpy.data.objects['Sphere']
    # sky_obj.name = 'Sky'
    
    # sky_mat = bpy.data.materials.new(name="SkyBox")
    # sky_mat.use_nodes = True
    # bsdf = sky_mat.node_tree.nodes["Principled BSDF"]
    
    # texImage = sky_mat.node_tree.nodes.new('ShaderNodeTexImage')
    # texture_dir = script_dir/"textures"/"beautiful-cloudy-sky.jpg"
    # texImage.image = bpy.data.images.load(str(texture_dir))
    # sky_mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    
    # sky_obj.data.materials.append(sky_mat)
    
    # sky_obj.rotation_euler[0] = 5.06145

def add_plane(prov_size):
    bpy.ops.mesh.primitive_plane_add(size=prov_size, location=[0, 0, 0])
    plane_obj = bpy.data.objects['Plane']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    mesh = plane_obj.data
    
    plane_obj.name = 'Floor'
    plane_obj.scale[0] = 2.3
    plane_obj.scale[1] = 2.175
    plane_obj.rotation_euler[0] = -1.5708
    
    mat = bpy.data.materials.new(name="FloorColor") #create new material and variable
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    matOutput = mat.node_tree.nodes["Material Output"]
    
    # texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    # texture_dir = script_dir/"textures"/"grass-texture-background.jpg"
    # texImage.image = bpy.data.images.load(str(texture_dir))
    # mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    
    # Mapping nodes
    texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
    texMapping = mat.node_tree.nodes.new('ShaderNodeMapping')
    # texMapping.inputs[3].default_value[0] = 4
    # texMapping.inputs[3].default_value[1] = 6
    mat.node_tree.links.new(texCoord.outputs['UV'], texMapping.inputs['Vector'])
    
    # Texture nodes
    texColorImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture2_dir =  script_dir/"textures"/"wood_floor"/"wood_floor_deck_diff_4k.jpg"
    texColorImage.image = bpy.data.images.load(str(texture2_dir))
    mat.node_tree.links.new(texMapping.outputs['Vector'], texColorImage.inputs['Vector'])
    
    texRoughImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture3_dir = script_dir/"textures"/"wood_floor"/"wood_floor_deck_rough_4k.exr"
    texRoughImage.image = bpy.data.images.load(str(texture3_dir))
    mat.node_tree.links.new(texMapping.outputs['Vector'], texRoughImage.inputs['Vector'])
    
    texNormalMapImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture4_dir = script_dir/"textures"/"wood_floor"/"wood_floor_deck_nor_gl_4k.exr"
    texNormalMapImage.image = bpy.data.images.load(str(texture4_dir))
    mat.node_tree.links.new(texMapping.outputs['Vector'], texNormalMapImage.inputs['Vector'])
    
    texDispImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture5_dir = script_dir/"textures"/"wood_floor"/"wood_floor_deck_disp_4k.png"
    texDispImage.image = bpy.data.images.load(str(texture5_dir))
    mat.node_tree.links.new(texMapping.outputs['Vector'], texDispImage.inputs['Vector'])
    
    # Normal Map and Displacement nodes
    normalMap = mat.node_tree.nodes.new('ShaderNodeNormalMap')
    mat.node_tree.links.new(texNormalMapImage.outputs['Color'], normalMap.inputs['Color'])
    
    dispalcement = mat.node_tree.nodes.new('ShaderNodeDisplacement')
    mat.node_tree.links.new(texDispImage.outputs['Color'], dispalcement.inputs['Height'])
    
    # Connections
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texColorImage.outputs['Color'])
    mat.node_tree.links.new(bsdf.inputs['Roughness'], texRoughImage.outputs['Color'])
    
    mat.node_tree.links.new(normalMap.outputs['Normal'], bsdf.inputs['Normal'])
    
    mat.node_tree.links.new(dispalcement.outputs['Displacement'], matOutput.inputs['Displacement'])
    
    # Add offset
    uv_layer = mesh.uv_layers.active.data
    row_offset = 0.2  # Adjust the amount of offset
    for i, loop in enumerate(uv_layer):
        uv = loop.uv
        if int(uv[1] * 10) % 2 == 0:  # Apply offset to alternate rows
            uv[0] += row_offset
    
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