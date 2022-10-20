# Retargeting process
The raw data has skeletons that are defined according to an unconventional pose. We wanted to change that pose to be a T-pose, which is an industry standard in animation. Particularly, it is recognizable, and easier to work with in 3D software. We processed the data so that the animations are defined according to a T-posed skeleton, and not the original one.

<p align="center">
  <img src="default_pose_comparison.png" alt="comparison between original and processed skeletal definition">
  <br>
  <i>Comparison between original and processed skeletal definition</i>
</p>

## Scripts used
`_data_mobu_tpose_bvh.py`
This script is used in Autodesk MotionBuilder. It imports a BVH from the dataset containing animation data, and extracts a single-frame T-posed skeleton from it for further processing. The T-pose is extracted by importing an FBX file of an avatar which was already T-posed by an animator. By doing so, it was easy to extract a T-posed skeleton from the animation data by copying over the rotation values of the FBX skeleton to the BVH skeleton. The extracted BVH skeleton is then saved to disk temporarily.

`_data_maya_freeze_transforms.py`
This script is executed in Autodesk Maya. It imports the extracted BVH skeleton from the previous step, and "freezes" the rotation values for all bones. What this does is that the rotation values of the bones are set to 0, effectively updating the default pose of the skeleton to be a T-pose. The updated skeleton is saved to disk temporarily.

`_data_mobu_plot_bvh.py`
This script is executed in Autodesk MotionBuilder. It takes the updated T-posed skeleton for which all rotation values are 0. The script also imports a BVH file from the dataset for which the animation data should be retargeted onto a T-posed skeleton. For this, the BVH skeleton and the T-posed skeleton were both [characterized](https://help.autodesk.com/view/MOBPRO/2022/ENU/?guid=GUID-12F7FCD3-004E-45E9-85B3-E42C7C51B2F7) in MotionBuilder. This allowed realtime transfer of the animation data from one skeleton to another. Next, the retargeted animation was "baked" using MotionBuilder's `Plot` function, which captures the retargeted data and sets it as keyframes for the new skeleton. The new skeleton is then exported as a BVH file which contains the retargeted animation for the whole take.

*Note: The specifics of the retargeting algorithm is unclear as it is done internally inside MotionBuilder (the source code is not available). Theoretically, the process should be done using Forward Kinematics, as no Inverse Kinematic constraints were specified.*

*Note: The script can also normalize the animation data, centering the retargeted skeleton to world origin on average \[0,0,0\] and orienting the retargeted skeleton to look in the direction of positive Z axis on average (right-hand XYZ, Y-up).*

`data_standardization_pipeline.py`
This script launches Autodesk Maya and MotionBuilder, and passes the other scripts as launch arguments to the programs. This script is more like a user-interface, as you can specify various arguments to control the execution of the different pipeline stages above.
