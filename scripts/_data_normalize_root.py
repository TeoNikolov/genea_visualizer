from pyfbsdk import *
from pyfbsdk_additions import *
import os
import math

# Set to False when trying to run script from within Maya
# Set to True to mimic command line arguments when reading the script as text (i.e. replace the argument placeholders externally using string.replace() )
USE_ARGS=False

if USE_ARGS:
    TAKE_NAME = "MOBU_ARG_TAKE_NAME"
    FILE_BVH = "MOBU_ARG_BVH_FILENAME"
    FILE_BVH_EXPORTED = "MOBU_ARG_BVH_EXPORTED_FILENAME"
else:
    raise RuntimeError("This script is templated and cnanot be executed directly. Its arguments should be set externally.")

def import_BVH(file_path, take_name, namespace):
    if not os.path.exists(file_path):
        raise FileNotFoundError('The file does not exist: ' + file_path)
    
    # import BVH to current take
    FBApplication().FileImport(file_path, False, True)
    
    # rename take for consistency
    FBSystem().CurrentTake.Name = take_name
    
    # cleanup namespaces
    objList = FBComponentList()
    FBFindObjectsByName("BVH:*", objList, True, False)
    for o in objList:
        o.ProcessObjectNamespace(FBNamespaceAction.kFBReplaceNamespace, "BVH", namespace)

    # remove extra reference node
    extra_ref_node = FBFindModelByLabelName(namespace + ':reference')
    if len(extra_ref_node.Children) != 1:
        raise RuntimeError('Talking With Hands reference node has mode than 1 child (assumes only 1 child/reference node)')
    extra_ref_node.Children[0].Parent = None
    extra_ref_node.FBDelete()
    FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
    FBSystem().Scene.Evaluate()

def normalize_root(namespace, samples):
    # compute sampling stride
    total_frames = FBSystem().CurrentTake.LocalTimeSpan.GetStop().GetFrame()
    frame_step = total_frames / samples
    
    # sample position and rotation values
    reference_bone = FBFindModelByLabelName(namespace + ':body_world')
    hip_bone = FBFindModelByLabelName(namespace + ':b_root')
    pos_acc = [0, 0, 0]
    fwd_acc = [0, 0, 0]
    for i in range(samples):
        frame = int(frame_step * i)
        FBPlayerControl().Goto(FBTime(0,0,0,frame))
        # position
        pos_acc[0] += reference_bone.Translation[0]
        pos_acc[1] += reference_bone.Translation[1]
        pos_acc[2] += reference_bone.Translation[2]
        # rotation
        fwd = FBVector4d()
        rot_mat = FBMatrix()
        hip_bone.GetMatrix(rot_mat, FBModelTransformationType.kModelRotation, True)    
        # rotate Z axis to obtain new forward vector (assumez Z is forward)
        FBVectorMatrixMult(fwd, rot_mat, FBVector4d(0,0,1,0))
        fwd[1] = 0
        fwd_acc[0] += fwd[0]
        fwd_acc[1] = 0
        fwd_acc[2] += fwd[2]

    # compute average position and forward vector (normalized)
    pos_acc = [x / samples for x in pos_acc]
    fwd_acc = [x / samples for x in fwd_acc]
    fwd_4d = FBVector4d(fwd_acc[0],fwd_acc[1],fwd_acc[2],0)
    fwd_norm = math.sqrt(FBDot(fwd_4d, fwd_4d))
    fwd_acc[0] = fwd_4d[0] / fwd_norm
    fwd_acc[1] = fwd_4d[1] / fwd_norm
    fwd_acc[2] = fwd_4d[2] / fwd_norm
    # compute angle between the average forward vector and the Z-axis unit vector
    angle = math.acos(FBDot(FBVector4d(0,0,1,0), FBVector4d(fwd_acc[0], fwd_acc[1], fwd_acc[2],0)))
    angle = angle * (180 / math.pi)    
    # if pointing towards X, invert the angle
    if fwd_acc[0] > 0:
        angle = -angle

    T_ref = reference_bone.Translation.GetAnimationNode()
    R_hip = hip_bone.Rotation.GetAnimationNode()

    # interpolate the keys linearly, not cubic as it does automatically
    T_ref.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    R_hip.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    
    ### process keyframes
    FBPlayerControl().GotoStart()
    i = -1
    while (i <= total_frames):
        # keyframe next frame pos and rot without changing their curves
        if i < total_frames:
            frame_next = FBTime(0,0,0,i+1)
            TX_ref_next = T_ref.Nodes[0].FCurve
            TY_ref_next = T_ref.Nodes[1].FCurve
            TZ_ref_next = T_ref.Nodes[2].FCurve
            TX_ref_next.KeyAdd(frame_next, TX_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            TY_ref_next.KeyAdd(frame_next, TY_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            TZ_ref_next.KeyAdd(frame_next, TZ_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RX_ref_next = R_hip.Nodes[0].FCurve
            RY_ref_next = R_hip.Nodes[1].FCurve
            RZ_ref_next = R_hip.Nodes[2].FCurve
            RX_ref_next.KeyAdd(frame_next, RX_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RY_ref_next.KeyAdd(frame_next, RY_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RZ_ref_next.KeyAdd(frame_next, RZ_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)

            # the next frame is the first frame, nothing more to process
            if i == -1:
                i = 0
                continue

        ### rotation
        # compute rotation matrix of "angle" degrees around the Y axis
        y_rot_mat = FBMatrix()
        FBRotationToMatrix(y_rot_mat, FBVector3d(0,angle,0), FBRotationOrder.kFBXYZ)
        # multiply rotation around Y axis with the current rotation
        rot_mat = FBMatrix()
        hip_bone.GetMatrix(rot_mat, FBModelTransformationType.kModelRotation, False)
        new_rot = FBVector3d()
        FBMatrixToRotation(new_rot, y_rot_mat * rot_mat)
        # set the new rotation
        hip_bone.SetVector(new_rot, FBModelTransformationType.kModelRotation, False)
        hip_bone.Rotation.Key()

        ### position
        original_pos = FBVector3d()
        reference_bone.GetVector(original_pos, FBModelTransformationType.kModelTranslation, False)
        # subtract the average position
        new_pos = FBVector4d(original_pos[0] - pos_acc[0], original_pos[1] - pos_acc[1], original_pos[2] - pos_acc[2],0)
        # rotate the position w.r.t the hip rotation from earlier
        new_pos_rot = FBVector4d()
        FBVectorMatrixMult(new_pos_rot, y_rot_mat, new_pos)
        new_pos_rot = FBVector3d(new_pos_rot[0], new_pos_rot[1], new_pos_rot[2])
        # set the new position
        reference_bone.SetVector(new_pos_rot, FBModelTransformationType.kModelTranslation, False)
        reference_bone.Translation.Key()

        FBPlayerControl().StepForward()
        i += 1
        
    # optimize curves with linear interpolation and unrolling filter to make values continuous
    unroll_filter = FBFilterManager().CreateFilter('Unroll Rotations')
    unroll_filter.Start = FBTime(0,0,0,0)
    unroll_filter.Stop = FBTime(0,0,0,total_frames)
    unroll_filter.Apply(hip_bone.Rotation.GetAnimationNode(), True)

def export_BVH(output_path, twh_frozen_namespace):
    # center the root so translation is baked to 0,0,0 in BVH spec (does not alter the animation data)
    FBPlayerControl().GotoStart()
    FBFindModelByLabelName(twh_frozen_namespace + ':body_world').SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    objList = FBComponentList()
    FBFindObjectsByName(twh_frozen_namespace + ":*", objList, True, False)
    for o in objList:
        o.Selected=True
        o.ProcessObjectNamespace(FBNamespaceAction.kFBRemoveAllNamespace, twh_frozen_namespace)
    FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
    FBSystem().Scene.Evaluate()
    FBApplication().FileExport(output_path)

TWH_NAMESPACE = "TWH"

# Import mocap animation
import_BVH(FILE_BVH, TAKE_NAME, TWH_NAMESPACE)
FBSystem().Scene.Evaluate()

# Normalize root
normalize_root(TWH_NAMESPACE, 250)

# Export
export_BVH(FILE_BVH_EXPORTED, TWH_NAMESPACE)
