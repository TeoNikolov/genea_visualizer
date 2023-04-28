# GENEA 2023 BVH Visualizer
<p align="center">
  <img src="demo.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server</i>
</p>

- [GENEA 2022 BVH Visualizer](#genea-2022-bvh-visualizer)
  * [Introduction](#introduction)
  * [Blender Script](#blender-script)
    + [Using Blender UI](#using-blender-ui)
    + [Using command line](#using-command-line)
  * [Miscellaneous scripts](#miscellaneous-scripts)
  * [Replicating the GENEA Challenge 2022 visualizations](#replicating-the-genea-challenge-2022-visualizations)
- [Citation](#citation)
- [Contact](#contact)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

## Introduction

This repository contains code that can be used to visualize BVH files (with optional audio) using Docker, Blender, and FFMPEG. The code was developed for the [GENEA Challenge 2022](https://genea-workshop.github.io/2022/), and enables reproducing the visualizations used for the challenge stimuli on most platforms. The system integrates Docker and Blender to provide a free and easy-to-use solution that requires as little manual setup as possible. Currently, we provide one interfaces that you can use to access the visualizations:

- Stand-alone, for using the supplied Blender script with an existing Blender installation

## Blender Script

The Blender script used by the (future) server can also be used directly inside Blender, either through a command line interface or Blender's user intarface. Using the script directly is useful if you have Blender installed on your system, and you want to play around with the visualizer.

### Using Blender UI

1. Make sure you have `Blender 2.93.9` installed (other versions may work, but this is *not guaranteed*).
  - You can install Blender from Steam. Set version to 2.93.x in the properties.
2. Start `Blender` and navigate to the `Scripting` panel above the 3D viewport.
3. In the panel on the right of the 3D viewport, press `Open` to navigate to the `blender_render_2023.py` script. This script is found inside the `celery-queue` folder.
4. Tweak the settings in `main()` below the comment block that reads "SET ARGUMENTS MANUALLY...".
5. When ready, run the script by pressing the "play" button at the top to render the scene (this can take a while, so try with fewer frames first).
6. The rendered video will be saved to the `ARG_OUTPUT_DIR` directory (defaults to the same folder as the BVH file).

### Using command line
It is likely that your machine learning pipeline outputs a bunch of BVH and WAV files, such as during hyperparameter optimization. Instead of processing each BVH/WAV file pair separately through Blender's UI yourself, call Blender with [command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) like this (on Windows):

`"<path to Blender executable>" -b --python "<path to 'blender_render_2023.py' script>" -- -i1 "<path to main agent BVH file>" -i2 "<path to interlocutor BVH file>" -a1 "<path to main agent WAV file>" -a2 "<path to interlocutor WAV file>" -v -d 600 -o <directory to save MP4 video in> -m <visualization mode>`

On Windows, you may write something like this (on Windows):

`& "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --python ./blender_render_2023.py -- -i1 "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap1.bvh" -i2 "C:\Users\Wolf\Documents\NN_Output\BVH_files\mocap2.bvh" -a1"C:\Users\Wolf\Documents\NN_Output\audio1.wav" -a2 "C:\Users\Wolf\Documents\NN_Output\audio2.wav" -v -d 600 -o "C:\Users\Wolf\Documents\NN_Output\Rendered\" -m "full_body"`

Tip: Tweak `--duration <frame count>`, to smaller values to decrease render time and speed up your testing.

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
