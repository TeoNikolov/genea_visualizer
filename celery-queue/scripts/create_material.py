import bpy
import os

def add_materials(work_dir, name):
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
    
def setup_subdivision_surface(char_mesh):    
    # nodes = mat.node_tree.nodes
    # links = mat.node_tree.links
    
    # bsdf_node = mat.node_tree.nodes["Principled BSDF"]
    # material_output = mat.node_tree.nodes["Material Output"]
    
    # for node in nodes:
    #     if node.type == 'TEX_IMAGE':
    #         texture_diffuse = node
    
    # Ensure there's an active object
    # obj = bpy.context.active_object
    # if not obj:
    #     print("Please select an object.")
    #     return

    # Add a Subdivision Surface modifier
    subdiv_modifier = char_mesh.modifiers.new(name="Subdivision Surface", type='SUBSURF')

    # Set Levels Viewport and Render values
    subdiv_modifier.levels = 3
    subdiv_modifier.render_levels = 3

def setup_geometry_nodes(char_mesh):
    # Ensure there's an active object with a material
    # obj = bpy.context.active_object
    # if not obj:
    #     print("Please select an object with a material.")
    #     return

    # Add a new geometry node group modifier
    print(char_mesh)
    mod = char_mesh.modifiers.new(name="Geo Norm Modifier", type='NODES')
    
    # Access the node group
    node_group = bpy.data.node_groups.new(name="Geo Norm Group", type='GeometryNodeTree')
    mod.node_group = node_group

    # Create nodes
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    normal_node = node_group.nodes.new(type='GeometryNodeInputNormal')
    store_named_attribute = node_group.nodes.new(type='GeometryNodeStoreNamedAttribute')
    
    # Position nodes
    group_input.location = (-200, 0)
    normal_node.location = (-200, -100)
    store_named_attribute.location = (0, 0)
    group_output.location = (200, 0)

    # Add sockets for group input and output
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')

    # Set default values for the Store Named Attribute node
    store_named_attribute.inputs['Name'].default_value = "norm"
    store_named_attribute.data_type = 'FLOAT_VECTOR'

    # Create connections
    links = node_group.links
    links.new(group_input.outputs['Geometry'], store_named_attribute.inputs['Geometry'])
    links.new(normal_node.outputs['Normal'], store_named_attribute.inputs['Value'])
    links.new(store_named_attribute.outputs['Geometry'], group_output.inputs['Geometry'])

# Define the function to be executed when the button is clicked
def setup_material_nodes(char_mesh, work_dir):
    # Ensure there's an active object with a material
    # obj = bpy.context.active_object
    # if not obj or not obj.active_material:
    #     print("Please select an object with a material.")
    #     return

    mat = char_mesh.material_slots[0].material
    print("Material: ", mat)

    # Set the displacement method to "Displacement and Bump"
    char_mesh.active_material.displacement_method = 'BOTH'

    # Get the existing nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    texture_diffuse = None
    bsdf_node = None
    for node in nodes:
        if node.type == 'TEX_IMAGE' and not texture_diffuse:
            texture_diffuse = node
        if node.type == 'BSDF_PRINCIPLED' and not bsdf_node:
            bsdf_node = node

    if not texture_diffuse or not bsdf_node:
        print("Material must have an Image Texture and a Principled BSDF node.")
        return

    material_output = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None)
    if not material_output:
        print("Material must have an Output node.")
        return

    # Add the new nodes
    texture_displacement = nodes.new(type='ShaderNodeTexImage')
    multiply_node = nodes.new(type='ShaderNodeVectorMath')
    multiply_node.operation = 'MULTIPLY'
    scale_node = nodes.new(type='ShaderNodeVectorMath')
    scale_node.operation = 'SCALE'
    attribute_node = nodes.new(type='ShaderNodeAttribute')
    rotate_mesh_node = nodes.new(type='ShaderNodeVectorRotate')
    value_node = nodes.new(type='ShaderNodeValue')
    divide_node = nodes.new(type='ShaderNodeMath')
    divide_node.operation = 'DIVIDE'

    # Position the nodes
    texture_diffuse.location      = (-600, 200)
    texture_displacement.location = (-600, -100)
    attribute_node.location       = (-600, -400)
    rotate_mesh_node.location     = (-400, -400)
    value_node.location           = (-200, -400)
    bsdf_node.location            = (-200, 200)
    multiply_node.location        = (-200, -200)
    divide_node.location          = (0, -400)
    scale_node.location           = (0, -200)
    material_output.location      = (200, -200)

    # Set values
    try:
        diffuse_filepath = os.path.join(work_dir, "textures\\SMPLX\\", str(texture_diffuse.image))
        if "smplx_texture_f_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_f_disp.png"
        elif "smplx_texture_m_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_m_disp.png"
        else:
            print(f"Could not determine displacement texture from filepath: {diffuse_filepath}")
            return

        if texture_filename not in bpy.data.images:
            texture_path = os.path.join(work_dir, "textures/SMPLX", texture_filename)
            texture_displacement.image = bpy.data.images.load(texture_path)
        else:
            texture_displacement.image = bpy.data.images[texture_filename]

    except RuntimeError:
        print(f"Failed to load texture: {texture_path}")
        return

    attribute_node.attribute_name = "norm"
    value_node.outputs['Value'].default_value = 10
    divide_node.inputs[1].default_value = 1000
    
    rotate_mesh_node.inputs[2].default_value = [1, 0, 0]
    rotate_mesh_node.inputs[3].default_value = 1.57

    # Create connections
    links.new(texture_diffuse.outputs['Color'], bsdf_node.inputs['Base Color'])
    links.new(bsdf_node.outputs['BSDF'], material_output.inputs['Surface'])
    links.new(texture_displacement.outputs['Color'], multiply_node.inputs[0])
    links.new(attribute_node.outputs['Vector'], rotate_mesh_node.inputs[0])
    links.new(rotate_mesh_node.outputs['Vector'], multiply_node.inputs[1])
    links.new(multiply_node.outputs['Vector'], scale_node.inputs['Vector'])
    links.new(value_node.outputs['Value'], divide_node.inputs[0])
    links.new(divide_node.outputs['Value'], scale_node.inputs['Scale'])
    links.new(scale_node.outputs['Vector'], material_output.inputs['Displacement'])