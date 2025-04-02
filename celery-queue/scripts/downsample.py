import os
from os.path import join
import numpy as np 

for file in os.listdir("1_wayne_0_1_1_sample_1"):
    if not file.endswith(".npz"): 
        continue
    orig_arr = np.load(join("1_wayne_0_1_1_sample_1", file), allow_pickle=True)
    poses_30fps = orig_arr["poses"][::2]
    trans_30fps = orig_arr["trans"][::2]
    np.savez(join("1_wayne_0_1_1_sample_1", file.replace(".npz", "_30fps.npz")),
             poses=poses_30fps,
             trans=trans_30fps)