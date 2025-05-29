import bpy
import re
import os

def setup_characters(actor1, actor2):
    arm1 = bpy.context.scene.objects[actor1]
    arm2 = bpy.context.scene.objects[actor2]
    arm1.location = [0, 0.75, 0]
    arm2.location = [0, 0.75, 0]
    
def remove_bone(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones: # deselect the other bones
        if bone.name == bone_name:
            armature.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    
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


def load_hair_and_mask(smplx_char, SCRIPT_DIR):
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