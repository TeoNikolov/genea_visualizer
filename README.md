# Table of Contents
- [Important Updates](#important-updates)
- [GENEA Challenge 2020 BVH visualizer](#genea-challenge-2020-bvh-visualizer)
- [GENEA Challenge 2022 BVH visualizer](#genea-challenge-2022-bvh-visualizer)
- [GENEA Challenge 2023 BVH visualizer](#genea-challenge-2023-bvh-visualizer)
- [GENEA Leaderboard 2025 SMPLX visualizer](#GENEA-Leaderboard-2025-SMPLX-visualizer)
  * [Introduction](#introduction)
  * [Blender Script](#blender-script)
    + [Setup Blender, SMPLX add-on and code](#Setup-Blender-SMPLX-add-on-and-code)
    + [Using Blender UI](#using-blender-ui)
    + [Using command line](#using-command-line)
  * [Miscellaneous scripts](#miscellaneous-scripts)
  * [Replicating the GENEA Challenge 2023 visualizations](#replicating-the-genea-challenge-2023-visualizations)
- [Citation](#citation)
- [Contact](#contact)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# Important Updates
**16-04-2025:** GENEA Leaderboard 2025
- Removed `BVH` support
- Added `SMPLX` support
- Updated command line arguments
- Update scene
- Update rendering

**14-06-2023:** The GENEA Challenge 2023 visualizer receives improved input and output handling of filenames. (The original pre-updated code given to participants can be found [in this release](https://github.com/TeoNikolov/genea_visualizer/releases/tag/genea2023_release_participants)):
- BVH and WAV audio file input args are now linked to the main agent and interlocutor:
  - `-i1` -> `-imb` (main agent BVH)
  - `-i2` -> `-iib` (interlocutor BVH)
  - `-a1` -> `-imw` (main agent WAV)
  - `-a2` -> `-iiw` (interlocutor WAV)
- A new "output name" arg `-n` must be specified by the user for handling filenames of intermediate and final output files:
  - Do not include periods (`.`) or slashes (`/`, `\`) in the value. For example, `-n "my_output"` is allowed, but `-n "my_output.mp4"` or `-n "my_directory/my_output"` is not. Output directory should be specified using the `-o` arg.
  - The final composited video no longer uses a hardcoded filename and will not be overwitten if a new composited video is rendered in the same directory as the first one. Instead, the composited video uses the value of `-n` as filename, with `.mp4` added at the end.

# GENEA Challenge 2020 BVH visualizer
The very first installment of the GENEA Challenge 2020 visualizer is hosted in a different repo: https://github.com/jonepatr/genea_visualizer

Thanks to [@AbelDoc](https://github.com/AbelDoc/), the visualizer received a minimal version that can be used locally. It is especially useful for batch-rendering BVH files and supports multiple rendering engines in Blender!

The code is hosted here: https://github.com/AbelDoc/GENEA_Visualiser_Local

# GENEA Challenge 2022 BVH visualizer
The GENEA Challenge 2022 visualizer is archived at the `archive_2022` branch: https://github.com/TeoNikolov/genea_visualizer/tree/archive_2022

# GENEA Challenge 2023 BVH visualizer
<p align="center">
  <img src="demo.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server. The indicators above the speakers hint to the viewer that the speaker is engaged in "active speech".</i>
</p>

# GENEA Leaderboard 2025 SMPLX visualizer

## Introduction

This repository contains code that can be used to visualize NPZ files (with optional audio) using Blender. The code was developed for the [GENEA Leaderboard 2025](https://genea-workshop.github.io/leaderboard/). Currently, we provide only one interface for rendering visualizations:

- Stand-alone, for using the supplied Blender script with an existing Blender installation

## Blender Script

The Blender script can be used directly inside Blender, either through a command line interface or Blender's user interface. Using the script directly is useful if you have Blender installed on your system, and you want to play around with the visualizer.
### Setup Blender, SMPLX add-on and code
1. Install Blender from Steam - current version 4.3.2
	- In Steam, open Blender properties and for `launch options` add `-con`, so when you have Blender open you can see the console output
2. Install addon from SMPLX - (used so far 20220623) current version 20241129 [Link](https://smpl-x.is.tue.mpg.de/download.php)
	- Scroll down and search for `Latest Release`
	- Download the .zip file
	- Open Blender -> Preferences -> Add-ons -> (top right arrow) `Install from Disk...`
	- Select the .zip file
3. Clone this [repository](https://github.com/TeoNikolov/genea_visualizer/tree/dev-2025)
	- Latest branch - `dev-2025`
	- Main files to look at `Genea_leaderboard.py` and `parser.py`
### Using Blender UI
1. Start `Blender` and navigate to the `Scripting` panel above the 3D viewport.
2. In the panel on the right of the 3D viewport, press `Open` to navigate to the `Genea_leaderboard.py` script. This script is found inside the `celery-queue` folder.
3. Tweaking the settings:
	- `LOC 545` below `[INFO] Script is running in Blender UI.`
	- In `main(...) - LOC 360`, below the comment block that reads "SET ARGUMENTS MANUALLY...", there are arguments that are taken from a config file `config.json`.
4. When ready, run the script by pressing the `Play` button at the top to render the scene (this can take a while, so try with fewer frames first).
5. The rendered video will be saved to the `ARG_OUTPUT_DIR` directory. Filename is taken from loaded filename, but can be taken from `ARG_OUTPUT_NAME`.
### Using command line
It is likely that your machine learning pipeline outputs a bunch of BVH and WAV files, such as during hyperparameter optimization. Instead of processing each BVH/WAV file pair separately through Blender's UI yourself, call Blender with [command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) like this (on Windows):

Open a terminal in the `celery_queue` folder and write:
`"<path to Blender executable>" -b --python "<path to 'Genea_leaderboard.py' script>" -- [arguments]`

Arguments are in `parser.py`:
- `-inf "<path to NPZ file>"`
	- `"C:\...\1_wayne_0_103_103.npz"`
- `-ind "<path to directory with multiple NPZ files>" `
	- `"C:\...\samples"` , samples will be taken from folder `samples`
- `-ina "<path to WAV files>"`
	- `"C:\...\beat_v2.0.0\beat_english_v2.0.0\wave16k"` 
- `-o <directory to save MP4 video in>`
	- `"C:\...\rendered"`, folder will contain all rendered samples
- `-s`, where to start rendering from. This can be a single int or array or ints
	- `0`, `"0, 346, 670"` - array length must match with `-d`
- `-d`, how many frames to render. This can be a single int or array of ints
	- `100`, `"150, 60, 90"` - array length must match with `-s`
	- a value of `-1` renders to the last of the sample
- `-v`, render a `MP4` in output folder
- `-p`, render a `PNG` in output folder
- `-rx`, X resolution for video (default: 1440)
- `-ry`, Y resolution for video (default:1080)

There is also a `config.json`, file that can hold some relevant values, so you don't need to write them every time

On Windows, you may write something like this:

`& "C:\...\Steam\steamapps\common\Blender\blender.exe" -b --python ./Genea_leaderboard.py -- -o "C:\...\rendered" -ind "C:\...\samples" -ina "C:\...\beat_v2.0.0\beat_english_v2.0.0\wave16k" -v -s 0 -d 10`

Tip: Tweak `-d, --duration <frame count>`, to smaller values to decrease render time and speed up your testing.
## Miscellaneous scripts
During the development of the visualizer, a variety of scripts were used for standardizing the data and processing video stimuli for subjective evaluation. The scripts are included in the `scripts` folder in case anyone needs to use them directly, or as reference, for solving similar tasks. Some scripts were not written in a user-friendly manner, and lack comments and argument parsing. Therefore, using some scripts may be cumbersome, so be ready for some manual fiddling (e.g. replacing hard-coded paths). Writing a short readme inside the scripts folder is on the backlog, but there is no telling when this will happen at the moment.

## Replicating the GENEA Challenge 2023 visualizations
Currently, the default settings written inside the Blender script indicate the settings that will be used to render the final challenge stimuli of GENEA Challenge 2023. Please check this repository occasionally for any changes to these settings.

# Citation
```
@inproceedings{kucherenko2023genea,
  author={Kucherenko, Taras and Nagy, Rajmund
    and Yoon, Youngwoo and Woo, Jieyeon
    and Nikolov, Teodor and Tsakov, Mihail
    and Henter, Gustav Eje},
  title={The {GENEA} {C}hallenge 2023: {A} large-scale
    evaluation of gesture generation models in
    monadic and dyadic settings},
  booktitle = {Proceedings of the ACM International
    Conference on Multimodal Interaction},
  publisher = {ACM},
  series = {ICMI '23},
  year={2023}
}
```

# Contact
To find more GENEA Challenge 2023 material on the web, please see:
* Challenge : https://genea-workshop.github.io/2023/challenge/
* Workshop : https://genea-workshop.github.io/2023/workshop/

To find more GENEA Challenge 2022 material on the web, please see:
* Summary page : https://youngwoo-yoon.github.io/GENEAchallenge2022/
* Challenge : https://genea-workshop.github.io/2022/challenge/
* Workshop : https://genea-workshop.github.io/2022/workshop/

If you have any questions or comments, please contact:
* Teodor Nikolov <tnikolov@hotmail.com>
* Mihail Tsakov <tsakovm@gmail.com>
* The GENEA Challenge & Workshop organisers <genea-contact@googlegroups.com>

