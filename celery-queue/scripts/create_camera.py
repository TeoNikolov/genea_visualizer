import bpy

def add_camera(cam_pos, cam_rot, name):
    bpy.ops.object.camera_add(enter_editmode=False, location=cam_pos, rotation=cam_rot)
    cam = bpy.data.objects['Camera']
    cam.scale = [5, 25, 5]
    cam.data.lens = 17.5
    if name == 'Main':
        cam.data.lens = 35
    cam.name = name + '_cam'
    bpy.context.scene.camera = cam # add cam so it's rendered
    
def get_camera(name):
    cam = bpy.data.objects[name]
    bpy.context.scene.camera = cam
