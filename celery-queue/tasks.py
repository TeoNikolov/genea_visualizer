# Copyright 2020 by Patrik Jonell.
# All rights reserved.
# This file is part of the GENEA visualizer,
# and is released under the GPLv3 License. Please see the LICENSE
# file that should have been included as part of this package.


import os
from celery import Celery
import subprocess
from celery.utils.log import get_task_logger
import requests
import tempfile
from pyvirtualdisplay import Display
from bvh import Bvh
import time
import ffmpeg
from pathlib import Path

Display().start()


logger = get_task_logger(__name__)


WORKER_TIMEOUT = int(os.environ["WORKER_TIMEOUT"])
celery = Celery(
	"tasks",
	broker=os.environ["CELERY_BROKER_URL"],
	backend=os.environ["CELERY_RESULT_BACKEND"],
)

class TaskFailure(Exception):
	pass


def validate_bvh_file(bvh_file):
	MAX_NUMBER_FRAMES = int(os.environ["MAX_NUMBER_FRAMES"])
	FRAME_TIME = 1.0 / float(os.environ["RENDER_FPS"])
	FRAME_EPSILON = 0.00001

	file_content = bvh_file.decode("utf-8")
	mocap = Bvh(file_content)
	counter = None
	for line in file_content.split("\n"):
		if counter is not None and line.strip():
			counter += 1
		if line.strip() == "MOTION":
			counter = -2

	if mocap.nframes != counter:
		raise TaskFailure(
			f"The number of rows with motion data ({counter}) does not match the Frames field ({mocap.nframes})"
		)

	if MAX_NUMBER_FRAMES != -1 and mocap.nframes > MAX_NUMBER_FRAMES:
		raise TaskFailure(
			f"The supplied number of frames ({mocap.nframes}) is bigger than {MAX_NUMBER_FRAMES}"
		)

	if mocap.frame_time < FRAME_TIME - FRAME_EPSILON or mocap.frame_time > FRAME_TIME + FRAME_EPSILON:
		raise TaskFailure(
			f"The supplied frame time ({mocap.frame_time}) differs from the required {FRAME_TIME} (+/- {FRAME_EPSILON})"
		)

@celery.task(name="tasks.render", bind=True, hard_time_limit=WORKER_TIMEOUT)
def render(self, bvh_file_uri: str, audio_file_uri: str, rotate_flag: str, visualization_mode: str) -> str:
	HEADERS = {"Authorization": f"Bearer " + os.environ["SYSTEM_TOKEN"]}
	API_SERVER = os.environ["API_SERVER"]

	logger.info("rendering..")
	self.update_state(state="PROCESSING")

	audio_file = requests.get(API_SERVER + audio_file_uri, headers=HEADERS).content if audio_file_uri is not None else None
	bvh_file = requests.get(API_SERVER + bvh_file_uri, headers=HEADERS).content
	validate_bvh_file(bvh_file)
	
	def call_blender_process(script_args):
		process = subprocess.Popen(
			[
				"/blender/blender-2.83.0-linux64/blender",
				"-b",
				"--python",
				"blender_render.py",
				"--",
			] + script_args,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
		)
		
		total = None
		current_frame = None
		for line in process.stdout:
			#print(line) # debug process prints
			line = line.decode("utf-8").strip()
			if line.startswith("total_frames "):
				_, total = line.split(" ")
				total = int(float(total))
			elif line.startswith("Append frame "):
				*_, current_frame = line.split(" ")
				current_frame = int(current_frame)
			elif line.startswith("output_file"):
				_, file_name = line.split(" ")
				return file_name
			if total and current_frame:
				self.update_state(
					state="RENDERING", meta={"current": current_frame, "total": total}
				)
		if process.returncode != 0:
			raise TaskFailure(process.stderr.read().decode("utf-8"))
	
	def call_ffmpeg_process(video_file, audio_file, output_file):
		if ".mp4" not in video_file:
			raise TaskFailure("Only MP4 video stream is currently supported!")
		if ".wav" not in audio_file:
			raise TaskFailure("Only WAV audio stream is currently supported!")
		
		self.update_state(
			state="COMBINING A/V"
		)

		# FFMPEG CMD ARGS --> ["ffmpeg", "-i", video_file, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_file]
		
		v_stream = ffmpeg.input(video_file)['v']
		a_stream = ffmpeg.input(audio_file)['a']
		output_ffmpeg = ffmpeg.output(v_stream, a_stream, output_file, vcodec='copy', acodec='aac', **{'shortest': None, 'y': None})
		ffmpeg_result = ffmpeg.run(output_ffmpeg, capture_stdout=True, capture_stderr=True)
		if ffmpeg_result[0] != b'':
			print("FFMPEG ERROR")
			raise TaskFailure(ffmpeg_result[0].decode("utf-8"))
		return output_file
		
	
	output_file = None
	output_dir = Path(tempfile.mkdtemp()) / "video"
	with tempfile.NamedTemporaryFile(suffix=".bvh") as tmp_bvh:
		tmp_bvh.write(bvh_file)
		tmp_bvh.seek(0)
		script_args = []
		script_args.append('--input1')
		script_args.append(tmp_bvh.name)
		script_args.append('--input2')
		script_args.append(tmp_bvh.name)
		script_args.append('--duration')
		script_args.append(os.environ["RENDER_DURATION_FRAMES"])
		script_args.append('--video')
		script_args.append('--png')
		script_args.append('--res_x')
		script_args.append(os.environ["RENDER_RESOLUTION_X"])
		script_args.append('--res_y')
		script_args.append(os.environ["RENDER_RESOLUTION_Y"])
		script_args.append('-o')
		script_args.append(output_dir)
		script_args.append('--visualization_mode')
		script_args.append(visualization_mode)
		if rotate_flag is not None:
			script_args.append('--rotate')
			script_args.append(rotate_flag)
		
		output_file = call_blender_process(script_args)
		if audio_file:
			with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_wav:
				tmp_wav.write(audio_file)
				tmp_wav.seek(0)
				output_file = call_ffmpeg_process(output_file, tmp_wav.name, os.path.join(os.path.dirname(output_file),"combined_av.mp4"))

	if output_file is None:
		raise TaskFailure("Something went wrong... Not sure why.")
		
	files = {"file": (os.path.basename(output_file), open(output_file, "rb"))}
	return requests.post(
		API_SERVER + "/upload_video", files=files, headers=HEADERS
	).text