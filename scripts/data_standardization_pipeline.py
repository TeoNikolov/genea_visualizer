# This script runs a pipeline to t-pose the skeletons of the TalkingWithHands (TWH) dataset, and export 30fps BVH animations.
# There are three main stages in this pipeline, each of which should be issued by specifying a flag in the command line.
# Make sure to set the paths to the MotionBuilder and Maya directories containing their executables (see further below).

# 1. (--tpose) Load MotionBuilder and import a T-posed FBX file containing the same skeletal structure as that found in the TWH dataset, as well as a BVH file containing the skeleton to be T-posed. The skeleton should be T-posed but MUST NOT have the joint rotations/orientations zeroed out (i.e. frozen). This is needed since rotations of the FBX skeleton are copied to the TWH skeleton, to preserve any differences in bone lengths. The t-posed skeleton is then exported as an FBX file.

# 2. (--freeze) Load Maya and import the FBX as exported from step 1. In Maya, the joint rotations and transformations are "frozen", which makes it that their rotation/orientation is set to 0 and becomes the new point of reference for the pose. This is essential in order to have a "proper" T-pose, where the pose is preserved after setting all joint rotations/orientations to 0. The T-posed skeleton is then exported to a new FBX file.

# 3. (--retarget) Load MotionBuilder and import the same BVH as in step 1, as well as the FBX file exported from step 2. This step retargets the original animation with the non-T-posed skeleton, to the correctly T-posed skeleton, using MotionBuilder's retargeting algorithm. The retargeted animation is plotted onto the T-posed skeleton, and exported as a 30FPS BVH file. The file contains the original animation as closely as possible with the original skeleton, except that the rest pose is now a proper T-pose.

# A link that helped figure out part of the code.
# https://discourse.techart.online/t/run-maya-and-execute-a-script/11999/7

import base64
import subprocess
import tempfile
import argparse
import sys
import os
from pathlib import Path

############################################################################################
# Change the paths to the MotionBuilder and Maya directories on your computer			   #
# The MotionBuilder and Maya directories contain the program executables (.exe on Windows) #
# Make sure to include a trailing slash at the end of the string						   #
############################################################################################

MAYA_DIR = 'C:/Program Files/Autodesk/Maya2022/bin/'
MOBU_DIR = 'C:/Program Files/Autodesk/MotionBuilder 2022/bin/x64/' # got MotionBuilder? If yes, set this to the directory containing the binary (include a trailing slash)

######################################################
# You do not need to change anything below this line #
######################################################

FILE_MOBU_TPOSE_SCRIPT = Path("_data_mobu_tpose_bvh.py").resolve().as_posix()
FILE_MOBU_PLOT_ANIM_SCRIPT = Path("_data_mobu_plot_bvh.py").resolve().as_posix()
FILE_MOBU_NORMALIZE_ROOT_SCRIPT = Path("_data_normalize_root.py").resolve().as_posix()
FILE_MAYA_FREEZE_SCRIPT = Path("_data_maya_freeze_transform.py").resolve().as_posix()
FILE_GENEA_FBX_ORIGINAL = Path("model/GenevaModel_v2_Tpose_texture-fix.fbx").resolve().as_posix() # or any other file containing the same skeletal structure as the TWH dataset, making sure the joint rotations/orientations in the T-pose ARE NOT ZEROED OUT - check stage 1 in the instructions above

# wrappers for launching MotionBuilder and Maya executables
def launch_mobu(mobu_path, python_script, run_batched=False, *additional_args):
	args = [mobu_path, '-suspendMessages', '-verbosePython', python_script]
	if run_batched:
		args.append('-batch')
	args.extend(str(i) for i in additional_args)
	subprocess.check_call(args)
def launch_maya(maya_path, python_script, *additional_args):
	encoded_python = base64.b64encode(python_script.encode('utf-8'))
	script_text = '''python("import base64; exec (base64.urlsafe_b64decode({}))")'''
	args = [maya_path, '-c', script_text.format(encoded_python)]
	args.extend(str(i) for i in additional_args)
	subprocess.check_call(args)

### load BVH in MoBu, export T-posed skeleton
def mobu_t_pose_BVH(mobu_dir, clip_name, file_bvh, file_genea_fbx, file_tpose_skeleton, python_script_path, run_batched=True):
	script_text = ""
	with open(python_script_path, 'r') as pf:
		script_text = pf.read()
		script_text = script_text.replace('USE_ARGS=False', 'USE_ARGS=True')
		script_text = script_text.replace('MOBU_ARG_TAKE_NAME', clip_name)
		script_text = script_text.replace('MOBU_ARG_BVH_FILENAME', file_bvh)
		script_text = script_text.replace('MOBU_ARG_GENEA_FILENAME', file_genea_fbx)
		script_text = script_text.replace('MAYA_ARG_FILE_TPOSED_SKELETON', file_tpose_skeleton)
	with tempfile.TemporaryDirectory() as td:
		temp_file = td + '\\temp_mobu_tpose.py'
		with open(temp_file, 'w') as tf:
			tf.writelines(script_text)
		launch_mobu(mobu_dir + 'motionbuilder.exe', temp_file, run_batched=run_batched)

### fix t-posed skeleton in Maya, export fixed skeleton
def maya_freeze_transforms(maya_dir, file_tpose_skeleton, file_frozen_skeleton, python_script_path, run_batched=True):
	with open(python_script_path, 'r') as pf:
		if run_batched:	executable = maya_dir + 'mayabatch.exe'
		else:			executable = maya_dir + 'maya.exe'
		python_script = pf.read()
		# configure script ARGS
		python_script = python_script.replace('USE_ARGS=False', 'USE_ARGS=True')
		python_script = python_script.replace('MAYA_ARG_FILE_TPOSED_SKELETON', file_tpose_skeleton)
		python_script = python_script.replace('MAYA_ARG_FILE_FROZEN_SKELETON', file_frozen_skeleton)
		launch_maya(executable, python_script, 7)

### import fixed skeleton in MoBu, retarget, plot animation, and export new BVH
def mobu_plot_animation(mobu_dir, clip_name, file_bvh, file_genea_fbx, file_frozen_skeleton, file_bvh_export, python_script_path, run_batched=True):
	script_text = ""
	with open(python_script_path, 'r') as pf:
		script_text = pf.read()
		script_text = script_text.replace('USE_ARGS=False', 'USE_ARGS=True')
		script_text = script_text.replace('MOBU_ARG_TAKE_NAME', clip_name)
		script_text = script_text.replace('MOBU_ARG_BVH_FILENAME', file_bvh)
		script_text = script_text.replace('MOBU_ARG_GENEA_FILENAME', file_genea_fbx)
		script_text = script_text.replace('MAYA_ARG_FILE_FROZEN_SKELETON', file_frozen_skeleton)
		script_text = script_text.replace('MOBU_ARG_BVH_EXPORTED_FILENAME', file_bvh_export)

	with tempfile.TemporaryDirectory() as td:
		temp_file = td + '\\temp_mobu_plot.py'
		with open(temp_file, 'w') as tf:
			tf.writelines(script_text)
		launch_mobu(mobu_dir + 'motionbuilder.exe', temp_file, run_batched=run_batched)

def mobu_normalize_root(mobu_dir, clip_name, file_bvh, file_bvh_facing, file_bvh_export, file_bvh_export_facing, python_script_path, is_dyadic, run_batched=True):
	script_text = ""
	with open(python_script_path, 'r') as pf:
		script_text = pf.read()
		script_text = script_text.replace('USE_ARGS=False', 'USE_ARGS=True')
		script_text = script_text.replace('MOBU_ARG_TAKE_NAME', clip_name)
		script_text = script_text.replace('MOBU_ARG_BVH_FILENAME', file_bvh)
		script_text = script_text.replace('MOBU_ARG_BVH_FACING_FILENAME', file_bvh_facing)
		script_text = script_text.replace('MOBU_ARG_BVH_EXPORTED_FILENAME', file_bvh_export)
		script_text = script_text.replace('MOBU_ARG_BVH_EXPORTED_FACING_FILENAME', file_bvh_export_facing)
		script_text = script_text.replace('MOBU_ARG_DYADIC', str(is_dyadic))

	with tempfile.TemporaryDirectory() as td:
		temp_file = td + '\\temp_mobu_normroot.py'
		with open(temp_file, 'w') as tf:
			tf.writelines(script_text)
		launch_mobu(mobu_dir + 'motionbuilder.exe', temp_file, run_batched=run_batched)

### optionally, clean up the resulting BVH by clamping the values (from scientific notation to 2-3 digits after decimal point) to reduce the size (by a factor of 2+, I think)
def cleanup_bvh_file():
	...

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("workdir", help="The directory to process files in.")
parser.add_argument("match-token", help="Specify a string to match all files intended for processing. It is best to set the token to a common string found at the end of the file, including the '.bvh' extension.")
parser.add_argument("-r", "--recursive", action='store_true', help="Process files in the directory recursively.")
parser.add_argument("-b", "--batched", action='store_true', help="")
parser.add_argument("--tpose", action='store_true', help="Launch Autodesk MotionBuilder and t-pose the .BVH skeleton to match the (non-zeroed) rotations of a t-posed FBX file containing the same skeleton. Exports a t-posed FBX of the BVH skeleton, non-zeroed.")
parser.add_argument("--freeze", action='store_true', help="Launch Autodesk Maya to zero the rotations and joint orientations of a skeleton as exported via setting the --tpose flag. Exports a skeleton with rotations and joint orients zeroed out (i.e. they are 'frozen').")
parser.add_argument("--retarget", action='store_true', help="Launch Autodesk MotionBuilder and retarget the animation of a BVH file with non-tposed skeleton, to a t-posed skeleton as exported using the --tpose and --freeze flags. Exports a 30 FPS BVH animation.")
parser.add_argument("--normalize-root", action='store_true', help="Normalize the root bone during retargeting so that the translation is around (0,0,0) on average, and rotation is pointing towards Z on average.")
parser.add_argument("-f", "--force", action='store_true', help="Forces the writing of files, possibly overwriting existing ones.")
parser.add_argument("-d", "--dyadic", action='store_true', help="Configure the script for processing data in a dyadic setting. Currently used during root normalization only.")
args = vars(parser.parse_args())

# remove trailing slash from work dir path
if args['workdir'][-1] == '/' or args['workdir'][-1] == '\\':
	args['workdir'] = args['workdir'][:-1]
args['workdir'] = Path(args['workdir']).resolve().as_posix()

for root, subdirs, files in os.walk(args['workdir']):
	for f in files:
		if args['match-token'] in f:
			ROOT_DIR = root.replace('\\', '/') + "/"
			CLIP_NAME = f.split('.bvh')[0]

			FILE_BVH                         = ROOT_DIR + CLIP_NAME + '.bvh'
			FILE_TPOSE_SKELETON              = ROOT_DIR + CLIP_NAME + '_TPOSED_SKELETON.fbx'
			FILE_FROZEN_SKELETON             = ROOT_DIR + CLIP_NAME + '_TPOSED_SKELETON-frozen.fbx'
			FILE_BVH_EXPORT                  = ROOT_DIR + CLIP_NAME + '-exported.bvh'
			FILE_BVH_NORMALIZE_EXPORT        = ROOT_DIR + CLIP_NAME + '-normalized.bvh'
			FILE_BVH_EXPORT_FACING           = '' # used in dyadic normalization
			FILE_BVH_NORMALIZE_EXPORT_FACING = '' # used in dyadic normalization

			if args["dyadic"]:
				matching_files = list(Path(ROOT_DIR).glob("*" + args['match-token'] + "*"))
				
				clip_name_faced = []
				for candidate_file in matching_files:
					if ("deep" in CLIP_NAME and "shallow" in str(candidate_file)) or ("shallow" in CLIP_NAME and "deep" in str(candidate_file)):
						clip_name_faced.append(candidate_file)

				if len(clip_name_faced) != 1:
					raise RuntimeError("There should be a single matching file for this clip.")

				FILE_BVH_EXPORT_FACING = (clip_name_faced[0].parent / (clip_name_faced[0].stem + "-exported.bvh")).as_posix()
				FILE_BVH_NORMALIZE_EXPORT_FACING = (clip_name_faced[0].parent / (clip_name_faced[0].stem + "-normalized-faced.bvh")).as_posix()

			print("BVH: Processing \"" + FILE_BVH + "\".")

			if args['tpose']:
				print('STAGE: T-Posing')
				if not os.path.exists(FILE_TPOSE_SKELETON) or args['force']:
					mobu_t_pose_BVH(MOBU_DIR, CLIP_NAME, FILE_BVH, FILE_GENEA_FBX_ORIGINAL, FILE_TPOSE_SKELETON, FILE_MOBU_TPOSE_SCRIPT, run_batched=args['batched'])
					if not os.path.exists(FILE_TPOSE_SKELETON):
						raise RuntimeError('ERROR: Stage 1 (t-posing) failed to export FBX of t-posed skeleton!')
				else:
					print("    Skipping. An exported file was found and the \"--force\" flag is not set.")

			if args['freeze']:
				print('STAGE: Freezing')
				if not os.path.exists(FILE_FROZEN_SKELETON) or args['force']:
					maya_freeze_transforms(MAYA_DIR, FILE_TPOSE_SKELETON, FILE_FROZEN_SKELETON, FILE_MAYA_FREEZE_SCRIPT, run_batched=args['batched'])
					if not os.path.exists(FILE_FROZEN_SKELETON):
						raise RuntimeError('ERROR: Stage 2 (freezing) failed to export FBX of frozen, t-posed skeleton!')
				else:
					print("    Skipping. An exported file was found and the \"--force\" flag is not set.")

			if args['retarget']:
				print('STAGE: Retargeting')
				if not os.path.exists(FILE_BVH_EXPORT) or args['force']:
					mobu_plot_animation(MOBU_DIR, CLIP_NAME, FILE_BVH, FILE_GENEA_FBX_ORIGINAL, FILE_FROZEN_SKELETON, FILE_BVH_EXPORT, FILE_MOBU_PLOT_ANIM_SCRIPT, run_batched=args['batched'])
					if not os.path.exists(FILE_BVH_EXPORT):
						raise RuntimeError('ERROR: Stage 3 (retargeting) failed to export a BVH of retargeted animation onto the frozen, t-posed skeleton!')
				else:
					print("    Skipping. An exported file was found and the \"--force\" flag is not set.")

			if args['normalize_root']:
				print('STAGE: Normalizing')
				if not os.path.exists(FILE_BVH_NORMALIZE_EXPORT) or (args["dyadic"] and not os.path.exists(FILE_BVH_NORMALIZE_EXPORT_FACING)) or args['force']:
					mobu_normalize_root(MOBU_DIR, CLIP_NAME, FILE_BVH_EXPORT, FILE_BVH_EXPORT_FACING, FILE_BVH_NORMALIZE_EXPORT, FILE_BVH_NORMALIZE_EXPORT_FACING, FILE_MOBU_NORMALIZE_ROOT_SCRIPT, args["dyadic"], run_batched=args['batched'])
					if not os.path.exists(FILE_BVH_NORMALIZE_EXPORT):
						raise RuntimeError('ERROR: Stage 4 (root normalization) failed to export a BVH file!')
				else:
					print("    Skipping. An exported file was found and the \"--force\" flag is not set.")

	if not args['recursive']:
		break
