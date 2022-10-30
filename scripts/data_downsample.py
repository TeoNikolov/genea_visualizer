import os
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("workdir", help="A relative or full path to the directory in which your data is located. Will output processed files in the same directory.")
parser.add_argument("-f", "--force", action='store_true', help="Forces the writing of files, possibly overwriting existing ones. Will not overwrite your original files.")
args = vars(parser.parse_args())
WORK_DIR = Path(args['workdir']).resolve().as_posix()

def process_bvh(source_file, target_file):
	print('Processing ' + source_file)
	with open(source_file, 'r') as sbvh:
		with open(target_file, 'w') as tbvh:
			line = ''
			lines = []
			while "MOTION" not in line:
				line = sbvh.readline()
				lines.append(line)

			line = sbvh.readline()
			framecount = int(line.strip().split(' ')[-1])
			framecount_target = (framecount - 1)//3
			lines.append('Frames: {}\n'.format(framecount_target))
			
			line = sbvh.readline()
			lines.append('Frame Time: 0.0333333333333\n')

			line = sbvh.readline()
			while line:
				line = sbvh.readline()
				lines.append(line)
				line = sbvh.readline()
				line = sbvh.readline()
		
			tbvh.writelines(lines)

for root, subdirs, files in os.walk(WORK_DIR):
	for f in files:
		if 'local.bvh' in f:
			source_bvh = root + '/' + f
			target_bvh = root + '/' + f.split('.bvh')[0] + '_30fps.bvh'
			# if the file has been made already and overwriting is not set to true
			if os.path.exists(target_bvh) and not args['force']:
				continue
			process_bvh(source_bvh, target_bvh)