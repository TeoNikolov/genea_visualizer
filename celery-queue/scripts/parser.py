import sys
from pathlib import Path as myPath
import json
import argparse
import bpy
import os

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]
    
def load_json_config(dir):
    config_path = myPath(str(dir) + '/config.json')
    if config_path.is_file():
        with open(config_path, 'r') as f:
            print(f"Loading config from {config_path}")
            return json.load(f)
    else:
        print(f'No config file found! {config_path}')
    return {}

def save_json_config(args_in):
    updated_config = {
        'input_npz': args_in['input_npz'],
        'input_npz_dir': args_in['input_npz_dir'],
        'input_npz_dataset_filename': args_in['input_npz_dataset_filename'],
        'input_npz_dataset_directory': args_in['input_npz_dataset_directory'],
        'input_main_bvh': args_in['input_main_bvh'],
        'input_intr_bvh': args_in['input_intr_bvh'],
        'input_main_wav': args_in['input_main_wav'],
        'input_intr_wav': args_in['input_intr_wav'],
        'output_dir': args_in['output_dir'],
        'output_name': args_in['output_name'],
        'start': args_in['start'],
        'duration': args_in['duration'],
        'png': False,
        'video': False,
        'visualization_mode': args_in['visualization_mode'],
        'res_x': args_in['res_x'],
        'res_y': args_in['res_y'],
        'framerate': args_in['framerate'],
        'render_time': False,
        'update_config': False,
    }
    
    # Convert all Path objects in the config to strings
    serializable_config = {
        k: str(v) if isinstance(v, myPath) else v
        for k, v in updated_config.items()
    }
    
    config_path = myPath(str(script_dir.parents[0]) + '/config.json')
    
    with open(config_path, 'w') as f:
        json.dump(serializable_config, f, indent=4)
        print(f"Config saved to {config_path}")

def parse_int_list(value):
    try:
        # Split string by comma and convert each part to int
        return [int(v.strip()) for v in value.split(',') if v.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid list of integers: '{value}'")

def parse_args():
    config = load_json_config(script_dir.parents[0])
    
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # INPUT
    parser.add_argument('-inf', '--input_npz', help='Input filename of the NPZ file.', type=myPath, default=config.get('input_npz') if 'input_npz' in config else None)
    parser.add_argument('-ind', '--input_npz_dir', help='Input directory with filenames of the NPZ format.', type=myPath, default=config.get('input_npz_dir') if 'input_npz_dir' in config else None)
    parser.add_argument('-ina', '--audo_wav', help='Input WAV audio file from NPZ.', type=myPath, default=config.get('audo_wav') if 'audo_wav' in config else None)
    # parser.add_argument('-idf', '--input_npz_dataset_filename', help='Input dataset filename.', type=myPath, default=config.get('input_npz_dataset_filename') if 'input_npz_dataset_filename' in config else None)
    # parser.add_argument('-idd', '--input_npz_dataset_directory', help='Input dataset directory.', type=myPath, default=config.get('input_npz_dataset_directory') if 'input_npz_dataset_directory' in config else None)
    parser.add_argument('-ibf', '--input_bvh', help='Input filename of the main agent BVH motion file.', type=myPath, default=config.get('input_bvh') if 'input_bvh' in config else None)
    parser.add_argument('-ibw', '--input_bvh_wav', help='Input filename of the main agent WAV audio file.', type=myPath, default=config.get('input_bvh_wav') if 'input_bvh_wav' in config else None)
    
    # OUTPUT
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=myPath, default=config.get('output_dir') if 'output_dir' in config else None)
    parser.add_argument('-n', '--output_name', help='The name to use when outputting intermediate and final files. No periods \".\" or slashes \"/\" / \"\\\" allowed.', type=myPath, default=config.get('output_name') if 'output_name' in config else None)
    
    # SETTINGS
    parser.add_argument('-s', '--start', 
                        help='Which frame to start rendering from.', 
                        type=parse_int_list, default=config.get('start') if 'start' in config else 0)
    parser.add_argument('-d', '--duration', 
                        help='How many consecutive frames to render.', 
                        type=parse_int_list, default=config.get('duration') if 'duration' in config else 0)
    parser.add_argument('-p', '--png', 
                        help='Renders the result in a PNG-formatted image.', 
                        action=argparse.BooleanOptionalAction, default=config.get('png') if 'png' in config else False)
    parser.add_argument('-v', '--video', 
                        help='Renders the result in an MP4-formatted video.', 
                        action=argparse.BooleanOptionalAction, default=config.get('video') if 'video' in config else False)
    parser.add_argument('-m', "--visualization_mode", 
                        help='The visualization mode to use for rendering.',
                        type=str, choices=['full_body', 'upper_body'], default=config.get('visualization_mode') if 'visualization_mode' in config else 'full_body')
    parser.add_argument('-rx', '--res_x', 
                        help='The horizontal resolution for the rendered videos.', 
                        type=int, default=config.get('res_x') if 'res_x' in config else 1440)
    parser.add_argument('-ry', '--res_y', 
                        help='The vertical resolution for the rendered videos.', 
                        type=int, default=config.get('res_y') if 'res_y' in config else 1080)
    parser.add_argument('-f', '--framerate', 
                        help='The requested framerate.', 
                        type=int, default=config.get('framerate') if 'framerate' in config else 30)
    parser.add_argument('-rt', '--render_time', 
                        help='Compute render time for folder', 
                        action=argparse.BooleanOptionalAction, default=config.get('render_time') if 'render_time' in config else False)
    
    # CONFIG
    parser.add_argument('-uc', '--update_config', help='Which frame to start rendering from.', action=argparse.BooleanOptionalAction, default=config.get('update_config') if 'update_config' in config else False)
    
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    
    final_args = vars(parser.parse_args(args=argv))

    if len(config) == 0 or final_args['update_config'] is True:
        save_json_config(final_args)
    
    return final_args

def check_args(args_in):
    if args_in['input_npz'] is None and args_in['input_npz_dir'] is None:
        print('You should provide either a .NPZ file or folder that contains .NPZ files only!')
        exit()
    
    # if args_in['input_npz_dataset_directory'] is None:
    #     print('Dataset folder not provided')
    #     if args_in['input_npz_dataset_filename'] is None:
    #         print('For post-processing provide a path to the dataset folder and/or filename!')
        
    if args_in['png'] is False and args_in['video'] is False:
        print('Output format not selected! Use -p for .png or -v for .mp4')
        exit()
    
    if args_in['output_dir'] is None:
        print('Please provide an output directory for your file!')
        exit()
    
    if args_in['input_bvh'] is not None:
        print('BVH support is not implemented! Please set in config as "null" or remove argument from commandline!')
        exit()
            
    for dur in args_in['duration']:
        if dur == -1 and args_in['video'] is True:
            print(f'-1 duration means the full sample will be rendered! {args_in["duration"]}')
        elif dur == 0 and args_in['video'] is True:
            print(f'One of the provided durations is 0! {args_in["duration"]}')
            exit()
    
    if len(args_in['duration']) != len(args_in['start']):
        print('Mismatch between start and duration array!')
        exit()
    
    # There should be some sort of input handling here to allow for exiting (setup should be printed), update/edit config file
    # input("Press Enter to continue...")