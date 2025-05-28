import bpy
from pathlib import Path as myPath
import importlib
import os
import numpy as np
import csv
import re

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]

import edit_character
importlib.reload(edit_character)

def load_audio(filepath, name):
    print(filepath)
    audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip' + str(name),
        filepath=filepath,
        channel=1,
        frame_start=1
    )
    audio_strip.mute = False
    
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
    
def check_files_npz(SMPLX_LOCATION, SMPLX_FILENAME, SMPLX_LOCATION_DATASET = None, SMPLX_FILENAME_DATASET = None, added_gender_in = "neutral") -> myPath:
    SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/' + str(SMPLX_FILENAME) + '.npz')
    smplx_loaded_data = np.load(SMPLX_TAKE, allow_pickle=True)
    
    # SMPLX_TAKE_DATASET = myPath(str(SMPLX_LOCATION_DATASET) + '/' + str(SMPLX_FILENAME_DATASET) + '.npz')
    
    # if SMPLX_FILENAME_DATASET is None:
    #     print(f'Provided dataset file is None! ', str(SMPLX_FILENAME_DATASET))
    #     SMPLX_FILENAME_DATASET = SMPLX_FILENAME
    #     print(f'Attempt to find file with same name in dataset! ', {SMPLX_FILENAME_DATASET})
    #     SMPLX_TAKE_DATASET = myPath(str(SMPLX_LOCATION_DATASET) + '/' + str(SMPLX_FILENAME_DATASET) + '.npz')
    #     print(f'File from dataset! ', str(SMPLX_TAKE_DATASET))
    
    # if not SMPLX_TAKE_DATASET.exists():
    #     print(f'Provided file not found! Attempt string comparison from filename IF filename structure is similar to dataset filenaming!')
    #     SMPLX_FILENAME_DATASET_clean = SMPLX_FILENAME_DATASET.rsplit('_sample_', 1)[0]
    #     SMPLX_TAKE_DATASET = myPath(str(SMPLX_LOCATION_DATASET) + '/' + str(SMPLX_FILENAME_DATASET_clean) + '.npz')
    
    # if not SMPLX_TAKE_DATASET.exists() or SMPLX_LOCATION_DATASET is None or SMPLX_FILENAME_DATASET is None:
    #     print(f'The dataset file does not exit! Ignore checking provided .NPZ file! {SMPLX_TAKE_DATASET}')
    #     return SMPLX_TAKE
    
    # smplx_dataset_data = np.load(SMPLX_TAKE_DATASET, allow_pickle=True)
    
    speaker = SMPLX_FILENAME.split("_")[1]
    speaker_heights = {'ayana': 1.09, 'carla': 1.36, 'carlos': 1.19, 'daiki': 1.34, 'goto': 1.12, 'hailing': 1.21, 'itoi': 1.26, 'jorge': 1.38, 
                       'katya': 1.12, 'kexin': 1.11, 'kieks': 1.29, 'lawrence': 1.28, 'li': 1.34, 'lu': 1.26, 'luqi': 1.21, 'miranda': 1.21, 'nidal': 1.41, 
                       'scott': 1.31, 'solomon': 1.45, 'sophie': 1.2, 'stewart': 1.33, 'tiffnay': 1.17, 'wayne': 1.38, 'yingqing': 1.2, 'zhao': 1.34}
    
    # CORRECT .NPZ
    os.makedirs(str(SMPLX_LOCATION) + '/body_shape', exist_ok=True)
    # if not os.path.isfile(os.path.join(str(SMPLX_LOCATION) + '/body_shape/', SMPLX_FILENAME)):
    
    added_gender = added_gender_in
    print('Gender should always be "neutral": ' + str(added_gender))
    
    added_model = 'smplx2020'
    print('Model: ' + str(added_model))
    
    if 'betas' not in smplx_loaded_data:
        added_betas = np.zeros(300, dtype=int)
    else:
        added_betas = smplx_loaded_data['betas']
    
    # if not np.allclose(speaker_heights[speaker], smplx_loaded_data['trans'][1][1], rtol=0.2):
        
        # min_len = smplx_loaded_data['trans'].shape[0]
        # if smplx_loaded_data['trans'].shape[0] != smplx_dataset_data['trans'].shape[0]:
        #     min_len = min(smplx_loaded_data['trans'].shape[0], smplx_dataset_data['trans'].shape[0])
        #     print('Shape does not match. Taking minimum frames! ' + str(min_len))
    
    print('Prev Trans: ' + str(smplx_loaded_data['trans']))
    temp = smplx_loaded_data['trans'].copy()
    offset = speaker_heights[speaker] - smplx_loaded_data['trans'][1][1]
    temp[:, 1] += offset
    added_trans = temp
    print('Trans: ' + str(added_trans))
    
    if 'expressions' not in smplx_loaded_data:
        added_expressions = np.zeros((len(smplx_loaded_data['poses']), 100), dtype=float)
        print('Expressions set to 0')
    else:
        added_expressions = smplx_loaded_data['expressions']
    print('Expressions: ' + str(added_expressions))
    
    if 'mocap_frame_rate' not in smplx_loaded_data:
        added_framrate = 30
        print('Framerate set to 30, since value is missing')
    else:
        added_framrate = smplx_loaded_data['mocap_frame_rate']
    print('Framerate: ' + str(added_framrate))
    
    if 'poses' not in smplx_loaded_data:
        print('This .NPZ does not contain any animation data!')
        exit()
    else:
        added_poses = smplx_loaded_data['poses']
    print('Poses: ' + str(added_poses))
    
    np.savez(os.path.join(str(SMPLX_LOCATION) + '/body_shape/', SMPLX_FILENAME),
                betas=added_betas, 
                poses=added_poses, 
                expressions=added_expressions,
                trans=added_trans,
                model=added_model,
                gender=added_gender,
                mocap_frame_rate=added_framrate)
    SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/body_shape/' + SMPLX_FILENAME + '.npz')
    print(SMPLX_TAKE)
    
    return SMPLX_TAKE

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