# GENEA 2022 BVH Visualizer
<p align="center">
  <img src="demo.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server</i>
</p>

- [GENEA 2022 BVH Visualizer](#genea-2022-bvh-visualizer)
  * [Introduction](#introduction)
  * [Server Solution](#server-solution)
    + [Limitations](#limitations)
    + [Build and start visualization server](#build-and-start-visualization-server)
    + [Using the visualization server](#using-the-visualization-server)
    + [example.py](#examplepy)
  * [Blender Script](#blender-script)
    + [Using Blender UI](#using-blender-ui)
    + [Using command line](#using-command-line)
  * [Miscellaneous scripts](#miscellaneous-scripts)
  * [Replicating the GENEA Challenge 2022 visualizations](#replicating-the-genea-challenge-2022-visualizations)
- [Citation](#citation)
- [Contact](#contact)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

## Introduction

This repository contains code that can be used to visualize BVH files (with optional audio) using Docker, Blender, and FFMPEG. The code was developed for the [GENEA Challenge 2022](https://genea-workshop.github.io/2022/), and enables reproducing the visualizations used for the challenge stimuli on most platforms. The system integrates Docker and Blender to provide a free and easy-to-use solution that requires as little manual setup as possible. Currently, we provide three interfaces that you can use to access the visualizations:

- Server, hosted by the GENEA organizers at http://129.192.81.237/
- Server, hosted locally by you using the files from this repository
- Stand-alone, for using the supplied Blender script with an existing Blender installation

Each BVH file can be visualized in one of two **visualization modes**:

- `full_body` : the avatar body is visible from below the knees to the head, with the original animation data left unchanged
- `upper_body` : the avatar body is visible from above the knees to the head, zoomed in, with fixed position and rotation for the hips and legs

When using the server/script, make sure to specify the visualization mode *exactly as formatted above*, in order to choose which visualization more you want to render for.

## Server Solution

*Most of the information below is needed to set up the server yourself. If you just want to use the GENEA-hosted server, scroll to [here](#examplepy).*

The Docker server consists of several containers which are launched together with the `docker-compose` command described below. The containers are:
* web: this is an HTTP server which receives render requests and places them on a "celery" queue to be processed.
* worker: this takes jobs from the "celery" queue and works on them. Each worker runs one Blender process, so increasing the amount of workers adds more parallelization
* monitor: this is a monitoring tool for celery. Default username is `user` and password is `password` (can be changed by setting `FLOWER_USER` and `FLOWER_PWD` when starting the docker-compose command)
* redis: needed for celery

### Limitations
1. The visualizer currently **does not support ARM systems**, like Mac M1. The issue stems from an ongoing [bug in QEMU](https://gitlab.com/qemu-project/qemu/-/issues/750), an emulation engine integrated into Docker, which messes with one of Blender's libraries.
2. For the server-based solution, you must install **Docker 20.10.14** (or later) on your machine.
3. For the Blender script-based solution, you must install **Blender 2.93.9** on your machine. *Other versions are not guaranteed to work!*
4. If passing an audio file with your HTTP request to the server, make sure the audio file is **equal or longer** than the video duration. The combining of video and audio streams uses the shortest stream, so a shorter audio will shorten the duration of the final video.

If you encounter any issues with the server or visualizer, please file an Issue in the repo. I will do my best to address it as soon as possible :)

### Build and start visualization server
First you need to install docker-compose:
`sudo apt  install docker-compose` (on Ubuntu)

You might want to edit some of the default parameters, such as the render resolution, in the `.env` file.

Then to start the server run `docker-compose up --build`

In order to run several (for example 3) workers (Blender renderers, which allows to parallelize rendering, run `docker-compose up --build --scale worker=3`

The `-d` flag can also be passed in order to run the server in the background. Logs can then be accessed by running `docker-compose logs -f`. Additionally it's possible to rebuild just the worker or API containers with minimal disruption in the running server by running for example `docker-compose up -d --no-deps --scale worker=2 --build worker`. This will rebuild the worker container and stop the old ones and start 2 new ones.

### Using the visualization server
The server is HTTP-based and works by uploading a bvh file, and optionally audio. You will then receive a "job id" which you can poll in order to see the progress of your rendering. When it is finished, you will get a URL to the video file, which you can download. Below are some examples using `curl`, and the [example.py](#examplepy) file contains a full python (3.7) example of how this can be used.

Since the server is available publicly online, a simple authentication system is included – just pass in the token `j7HgTkwt24yKWfHPpFG3eoydJK6syAsz` with each request. This can be changed by modifying `USER_TOKEN` in `.env`.

Depending on where you host the visualization, `SERVER_URL` might be different. If you just are running it locally on your machine you can use `127.0.0.1` but otherwise you would use the ip address to the machine that is hosting the server.

```curl -XPOST -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" -F "p_rotate=default" -F "visualization_mode=full_body OR upper_body" -F "file=@/path/to/bvh/file.bvh" http://SERVER_URL/render``` 
will return a URI to the current job `/jobid/[JOB_ID]`.

`curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/jobid/[JOB_ID]` will return the current job state, which might be any of:
* `{result": {"jobs_in_queue": X}, "state": "PENDING"}`: Which means the job is in the queue and waiting to be rendered. The `jobs_in_queue` property is the total number of jobs waiting to be executed. The order of job execution is not guaranteed, which means that this number does not reflect how many jobs there are before the current job, but rather reflects if the server is currently busy or not.
* `{result": null, "state": "PROCESSING"}`: The job is currently being processed. Depending on the file size this might take a while, but this acknowledges that the server has started to work on the request.
* `{result":{"current": X, "total": Y}, "state": "RENDERING"}`: The job is currently being rendered. Here, `current` shows which is the last rendered frame and `total` shows how many frames in total this job will render.
* `{result": null, "state": "COMBINING A/V"}`: The job is currently combining video and audio streams. This can occur only if an audio file was passed to the server alongside the BVH file. This is usually fast.
* `{"result": FILE_URL, "state": "SUCCESS"}`: The job ended successfully and the video is available at `http://SERVER_URL/[FILE_URL]`.
* `{"result": ERROR_MSG, "state": "FAILURE"}`: The job ended with a failure and the error message is given in `results`.

In order to retrieve the video, run `curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/[FILE_URL] -o result.mp4`. Please note that the server will delete the file after you retrieve it, so you can only retrieve it once!

### example.py

For the GENEA-hosted server at http://129.192.81.237/, the majority of the steps above have been done already. All you need to do is to contact the server and send your own files for rendering. The included `example.py` file provides an example for doing so, which you can call with a command like this (on Windows):

`python ./example.py <path to .BVH file> -a <path to .WAV file> -o <path to save .MP4 file to> -m <visualization mode> -s <IP where the server is hosted>`

**To contact the GENEA-hosted server**, and render a BVH file with audio, you may write a command like this (on Windows):

`python ./example.py "C:\Users\Wolf\Documents\NN_Output\BVH_Files\mocap.bvh" -a "C:\Users\Wolf\Documents\NN_Output\WAV_Files\audio.wav" -o "C:\Users\Wolf\Documents\NN_Output\Rendered\video.mp4" -m "full_body" -s http://129.192.81.237`

Note: The solution currently does not support the manual setting of number of frames to render from the client (`example.py`). Instead, make sure your BVH file is as long as you need it to, since this is what will get rendered by the server (capped at 2 minutes or 3600 frames).

## Blender Script

The Blender script used by the server can also be used directly inside Blender, either through a command line interface or Blender's user intarface. Using the script directly is useful if you have Blender installed on your system, and you want to play around with the visualizer.

### Using Blender UI

1. Make sure you have `Blender 2.93.9` installed (other versions may work, but this is *not guaranteed*).
2. Start `Blender` and navigate to the `Scripting` panel above the 3D viewport.
3. In the panel on the right of the 3D viewport, press `Open` to navigate to the `blender_render.py` script. This script is found inside the `celery-queue` folder.
4. Tweak the settings in `main()` below the comment block that reads "SET ARGUMENTS MANUALLY...".
5. When ready, run the script by pressing the "play" button at the top to render the scene (this can take a while, so try with fewer frames first).
6. The rendered video will be saved to the `ARG_OUTPUT_DIR` directory (defaults to the same folder as the BVH file).

### Using command line
It is likely that your machine learning pipeline outputs a bunch of BVH and WAV files, such as during hyperparameter optimization. Instead of processing each BVH/WAV file pair separately through Blender's UI yourself, call Blender with [command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) like this (on Windows):

`"<path to Blender executable>" -b --python "<path to 'blender_render.py' script>" -- -i "<path to BVH file>" -a "<path to WAV file>" -v -o <directory to save MP4 video in> -m <visualization mode>`

On Windows, you may write something like this (on Windows):

`& "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --python ./blender_render.py -- -i "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap.bvh" -a "C:\Users\Wolf\Documents\NN_Output\audio.wav" -v -o "C:\Users\Wolf\Documents\NN_Output\Rendered\" -m "full_body"`

Tip: Tweak `--duration <frame count>`, `--res_x <value>`, and `--res_y <value>`, to smaller values to decrease render time and speed up your testing.

## Miscellaneous scripts
During the development of the visualizer, a variety of scripts were used for standardizing the data and processing video stimuli for subjective evaluation. The scripts are included in the `scripts` folder in case anyone needs to use them directly, or as reference, for solving similar tasks. Some scripts were not written in a user-friendly manner, and lack comments and argument parsing. Therefore, using some scripts may be cumbersome, so be ready for some manual fiddling (e.g. replacing hard-coded paths). Writing a short readme inside the scripts folder is on the backlog, but there is no telling when this will happen at the moment.

## Replicating the GENEA Challenge 2022 visualizations
The parameters in the enclosed `.env` file correspond to the those used for rendering the final evaluation stimuli of the GENEA Challenge 2022, for ease of replication. As long as you clone this repo, build it using Docker, and input the BVH files used for the final visualization, you should be able to reproduce the results.


# Citation
If you use this material, please cite our latest paper on the GENEA Challenge 2022. At the time of writing (2022-07-29) this is our ACM ICMI 2022 paper. You can use the following BibTeX code to cite that work:

```
@inproceedings{yoon2022genea,
  author={Yoon, Youngwoo and Wolfert, Pieter and Kucherenko, Taras and Viegas, Carla and Nikolov, Teodor and Tsakov, Mihail and Henter, Gustav Eje},
  title={{T}he {GENEA} {C}hallenge 2022: {A} large evaluation of data-driven co-speech gesture generation},
  booktitle={Proceedings of the ACM International Conference on Multimodal Interaction},
  publisher={ACM},
  series={ICMI '22},
  year={2022}
}
```

# Contact
To find more GENEA Challenge 2022 material on the web, please see:
* https://youngwoo-yoon.github.io/GENEAchallenge2022/
* https://genea-workshop.github.io/2022/challenge/

If you have any questions or comments, please contact:
* Teodor Nikolov <tnikolov@hotmail.com>
* Mihail Tsakov <tsakovm@gmail.com>
* The GENEA Challenge & Workshop organisers <genea-contact@googlegroups.com>
