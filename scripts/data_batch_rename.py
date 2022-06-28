import base64
import subprocess
import tempfile
import argparse
import sys
import os

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("workdir", help="The directory to process files in.")
parser.add_argument("type", help="The type of rename operation.", choices=["rename_exported"])
parser.add_argument("-r", "--recursive", action='store_true', help="Process files in the directory recursively.")
args = vars(parser.parse_args())

# remove trailing slash from work dir path
if args['workdir'][-1] == '/' or args['workdir'][-1] == '\\':
	args['workdir'] = args['workdir'][:-1]

for root, subdirs, files in os.walk(args['workdir']):
	for f in files:
		filepath = os.path.join(root, f)
		if args['type'] == 'rename_exported':
			os.rename(filepath, filepath.replace('-exported.bvh', '.bvh'))
		else:
			raise NotImplementedError("The current rename operation is not supported ({}).".format(args['type']))

		# if 'session' not in f and f.split('.')[-1] in RENAMABLE_EXTENSIONS:
			# session_id = root.split('/')[-1].split('_')[-2]
			# os.rename(root + '/' + f, root + '/' + session_id + '_' + f)
	if not args['recursive']:
		break