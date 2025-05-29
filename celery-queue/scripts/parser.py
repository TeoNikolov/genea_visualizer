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

def parse_int_list(value):
    try:
        # Split string by comma and convert each part to int
        return [int(v.strip()) for v in value.split(',') if v.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid list of integers: '{value}'")

def parse_args():    
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # INPUT
    parser.add_argument('-inf', '--input_npz', 
                        help='Input filename of the NPZ file.', 
                        type=myPath, default=None)
    parser.add_argument('-ind', '--input_npz_dir', 
                        help='Input directory with filenames of the NPZ format.', 
                        type=myPath, default=None)
    parser.add_argument('-ina', '--audo_wav', 
                        help='Input WAV audio file from NPZ.', 
                        type=myPath, default=None)
    # parser.add_argument('-idf', '--input_npz_dataset_filename', 
    #                     help='Input dataset filename.', 
    #                     type=myPath, default=None)
    # parser.add_argument('-idd', '--input_npz_dataset_directory', 
    #                     help='Input dataset directory.', 
    #                     type=myPath, default=None)
    parser.add_argument('-ibf', '--input_bvh', 
                        help='Input filename of the main agent BVH motion file.', 
                        type=myPath, default=None)
    parser.add_argument('-ibw', '--input_bvh_wav', 
                        help='Input filename of the main agent WAV audio file.', 
                        type=myPath, default=None)
    
    # OUTPUT
    parser.add_argument('-o', '--output_dir', 
                        help='Output directory. Will use "<script directory/output/" if not specified.', 
                        type=myPath, default=None)
    parser.add_argument('-n', '--output_name', 
                        help='Output name. No periods \".\" or slashes \"/\" / \"\\\" allowed.', 
                        type=myPath, default=None)
    
    # SETTINGS
    parser.add_argument('-s', '--start', 
                        help='Which frame to start rendering from.', 
                        type=parse_int_list, default=0)
    parser.add_argument('-d', '--duration', 
                        help='How many consecutive frames to render.', 
                        type=parse_int_list, default=0)
    parser.add_argument('-p', '--png', 
                        help='Renders the result in a PNG-formatted image.', 
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('-v', '--video', 
                        help='Renders the result in an MP4-formatted video.', 
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('-m', "--visualization_mode", 
                        help='The visualization mode to use for rendering.',
                        type=str, choices=['full_body', 'upper_body'], default='full_body')
    parser.add_argument('-rx', '--res_x', 
                        help='The horizontal resolution for the rendered videos.', 
                        type=int, default=1440)
    parser.add_argument('-ry', '--res_y', 
                        help='The vertical resolution for the rendered videos.', 
                        type=int, default=1080)
    parser.add_argument('-f', '--framerate', 
                        help='The requested framerate.', 
                        type=int, default=30)
    parser.add_argument('-rt', '--render_time', 
                        help='Compute render time for folder', 
                        action=argparse.BooleanOptionalAction, default=False)
    
    argv = sys.argv
    
    # argv starts with [blender.exe, '-con', '--debug-memory'], which is len of 3
    if (len(argv) <= 3):
        return vars()
    
    argv = argv[argv.index("--") + 1 :]
    
    final_args = vars(parser.parse_args(args=argv))
    
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