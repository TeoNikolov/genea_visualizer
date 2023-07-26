# Table of Contents
- [Important Updates](#important-updates)
- [GENEA Challenge 2020 BVH visualizer](#genea-challenge-2020-bvh-visualizer)
- [GENEA Challenge 2022 BVH visualizer](#genea-challenge-2022-bvh-visualizer)
- [GENEA Challenge 2023 BVH visualizer](#genea-challenge-2023-bvh-visualizer)
  * [Introduction](#introduction)
  * [Blender Script](#blender-script)
    + [Using Blender UI](#using-blender-ui)
    + [Using command line](#using-command-line)
  * [Miscellaneous scripts](#miscellaneous-scripts)
  * [Replicating the GENEA Challenge 2023 visualizations](#replicating-the-genea-challenge-2023-visualizations)
- [Citation](#citation)
- [Contact](#contact)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# Important Updates
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

## Introduction

This repository contains code that can be used to visualize BVH files (with optional audio) using Blender for dyadic interactions. The code was developed for the [GENEA Challenge 2023](https://genea-workshop.github.io/2023/challenge/), and enables reproducing the visualizations used for the challenge stimuli on most platforms. Currently, we provide only one interface for rendering visualizations:

- Stand-alone, for using the supplied Blender script with an existing Blender installation

## Blender Script

The Blender script can be used directly inside Blender, either through a command line interface or Blender's user interface. Using the script directly is useful if you have Blender installed on your system, and you want to play around with the visualizer.

### Using Blender UI

1. Make sure you have `Blender 2.93.9` installed (other versions may work, but this is *not guaranteed*).
   - You can install Blender from Steam. Set version to 2.93.x in the properties.
2. Start `Blender` and navigate to the `Scripting` panel above the 3D viewport.
3. In the panel on the right of the 3D viewport, press `Open` to navigate to the `blender_render_2023.py` script. This script is found inside the `celery-queue` folder.
4. Tweak the settings in `main()` below the comment block that reads "SET ARGUMENTS MANUALLY...".
5. When ready, run the script by pressing the "play" button at the top to render the scene (this can take a while, so try with fewer frames first).
6. The rendered video will be saved to the `ARG_OUTPUT_DIR` directory (defaults to the same folder as the BVH file). Filename is computed from `ARG_OUTPUT_NAME`.

### Using command line
It is likely that your machine learning pipeline outputs a bunch of BVH and WAV files, such as during hyperparameter optimization. Instead of processing each BVH/WAV file pair separately through Blender's UI yourself, call Blender with [command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) like this (on Windows):

`"<path to Blender executable>" -b --python "<path to 'blender_render_2023.py' script>" -- -imb "<path to main agent BVH file>" -iib "<path to interlocutor BVH file>" -imw "<path to main agent WAV file>" -iiw "<path to interlocutor WAV file>" -v -d 600 -o <directory to save MP4 video in> -n "<output file name>" -m <visualization mode>`

On Windows, you may write something like this (on Windows):

`& "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --python ./blender_render_2023.py -- -imb "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap1.bvh" -iib "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap2.bvh" -imw "C:\Users\Wolf\Documents\NN_Output\audio1.wav" -iiw "C:\Users\Wolf\Documents\NN_Output\audio2.wav" -v -d 600 -o "C:\Users\Wolf\Documents\NN_Output\Rendered\" -n "Output" -m "full_body"`

Tip: Tweak `--duration <frame count>`, to smaller values to decrease render time and speed up your testing.

## Miscellaneous scripts
During the development of the visualizer, a variety of scripts were used for standardizing the data and processing video stimuli for subjective evaluation. The scripts are included in the `scripts` folder in case anyone needs to use them directly, or as reference, for solving similar tasks. Some scripts were not written in a user-friendly manner, and lack comments and argument parsing. Therefore, using some scripts may be cumbersome, so be ready for some manual fiddling (e.g. replacing hard-coded paths). Writing a short readme inside the scripts folder is on the backlog, but there is no telling when this will happen at the moment.

## Replicating the GENEA Challenge 2023 visualizations
Currently, the default settings written inside the Blender script indicate the settings that will be used to render the final challenge stimuli of GENEA Challenge 2023. Please check this repository occasionally for any changes to these settings.

# Citation
*TBD*

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

