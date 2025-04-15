# import numpy as np
# import os
# from os.path import join


# INPUT_DIR = "S:\Work\GENEA\GENEA2024\Team submissions\The_Semantic_Gesticulator\data1\zhangzeyi\SG_results_for_GENEA\save_res_all_only_bvh_with_root_height" # ...
# OUTPUT_DIR = "S:\Work\GENEA\GENEA2024\Team submissions\The_Semantic_Gesticulator\check"# ...

# os.makedirs(OUTPUT_DIR, exist_ok=True)

# for file in os.listdir(INPUT_DIR):
#     if not file.endswith(".npz"):
#         continue

#     arr = {**np.load(join(INPUT_DIR, file), allow_pickle=True)}

#     # Adjust root height
#     arr["trans"] /= [1, 100, 1]

#     # Downsample
#     arr["poses"] = arr["poses"][::2]
#     arr["trans"] = arr["trans"][::2]
    
#     np.savez(join(OUTPUT_DIR, file),
#              **arr)
    
import numpy as np
import os
from os.path import join


INPUT_DIR =  "S:/Work/GENEA/GENEA2024/Team submissions/DiffuseStyleGesture/original"
OUTPUT_DIR = "S:/Work/GENEA/GENEA2024/Team submissions/DiffuseStyleGesture/check"

speaker_heights = {'ayana': 1.09, 'carla': 1.36, 'carlos': 1.19, 'daiki': 1.34, 'goto': 1.12, 'hailing': 1.21, 
                   'itoi': 1.26, 'jorge': 1.38, 'katya': 1.12, 'kexin': 1.11, 'kieks': 1.29, 'lawrence': 1.28, 
                   'li': 1.34, 'lu': 1.26, 'luqi': 1.21, 'miranda': 1.21, 'nidal': 1.41, 'scott': 1.31, 'solomon': 1.45, 
                   'sophie': 1.2, 'stewart': 1.33, 'tiffnay': 1.17, 'wayne': 1.38, 'yingqing': 1.2, 'zhao': 1.34}

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in sorted(os.listdir(INPUT_DIR)):
    if not file.endswith(".npz"):
        continue

    arr = {**np.load(join(INPUT_DIR, file), allow_pickle=True)}
    # Adjust root height
    speaker = file.split("_")[1]
    arr["trans"] += [0, speaker_heights[speaker], 0]
    
    np.savez(join(OUTPUT_DIR, file),
             **arr)