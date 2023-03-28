from pyfbsdk import *
from pyfbsdk_additions import *
import os
import math

# The script is NOT intended to be used standalone, and may crash because its argument values are not set.
# The script should be executed externally via "data_standardization_pipeline.py", which will set the value of this script's arguments.
USE_ARGS=False

if USE_ARGS:
    TAKE_NAME                = "MOBU_ARG_TAKE_NAME"
    FILE_BVH                 = "MOBU_ARG_BVH_FILENAME"
    FILE_BVH_FACING          = "MOBU_ARG_BVH_FACING_FILENAME" # can be empty ("") if DYADIC = False
    FILE_BVH_EXPORTED        = "MOBU_ARG_BVH_EXPORTED_FILENAME"
    FILE_BVH_EXPORTED_FACING = "MOBU_ARG_BVH_EXPORTED_FACING_FILENAME" # can be empty ("") if DYADIC = False
    DYADIC                   = MOBU_ARG_DYADIC
else:
    raise RuntimeError("This script is templated and cannot be executed directly. Its arguments must be set externally.")

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
    FBSystem().Scene.NamespaceCleanup()

def normalize_root(namespace_target, namespace_facing, is_dyadic, samples):
    # compute sampling stride
    total_frames = FBSystem().CurrentTake.LocalTimeSpan.GetStop().GetFrame()
    frame_step = total_frames / samples
    
    # bone references
    target_refbone = FBFindModelByLabelName(namespace_target + ':body_world')
    target_hipbone = FBFindModelByLabelName(namespace_target + ':b_root')
    T_refT = target_refbone.Translation.GetAnimationNode()
    R_hipT = target_hipbone.Rotation.GetAnimationNode()
    if is_dyadic:
        facing_refbone = FBFindModelByLabelName(namespace_facing + ':body_world') if is_dyadic else None
        facing_hipbone = FBFindModelByLabelName(namespace_facing + ':b_root')     if is_dyadic else None
        T_refF = facing_refbone.Translation.GetAnimationNode()
        R_hipF = facing_hipbone.Rotation.GetAnimationNode()

    # sample "target" position and rotation values
    pos_acc = [0, 0, 0]
    fwd_acc = [0, 0, 0]
    for i in range(samples):
        frame = int(frame_step * i)
        FBPlayerControl().Goto(FBTime(0,0,0,frame))
        # position
        pos_acc[0] += target_refbone.Translation[0]
        pos_acc[1] += target_refbone.Translation[1]
        pos_acc[2] += target_refbone.Translation[2]
        # rotation
        fwd = FBVector4d()
        rot_mat = FBMatrix()
        target_hipbone.GetMatrix(rot_mat, FBModelTransformationType.kModelRotation, True)    
        # rotate Z axis to obtain new forward vector (assumez Z is forward)
        FBVectorMatrixMult(fwd, rot_mat, FBVector4d(0,0,1,0))
        fwd[1] = 0
        fwd_acc[0] += fwd[0]
        fwd_acc[1] = 0
        fwd_acc[2] += fwd[2]

    # compute "target" average position and forward vector (normalized)
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
    # compute a rotation matrix
    y_rot_mat = FBMatrix()
    FBRotationToMatrix(y_rot_mat, FBVector3d(0,angle,0), FBRotationOrder.kFBXYZ)

    # interpolate the keys linearly, not cubic as it does automatically
    T_refT.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    R_hipT.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
    if is_dyadic:
        T_refF.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear
        R_hipF.DefaultInterpolation = FBInterpolation.kFBInterpolationLinear

    ### process keyframes
    FBPlayerControl().GotoStart()
    i = -1
    while (i <= total_frames):
        # keyframe next frame pos and rot without changing their curves
        if i < total_frames:
            frame_next = FBTime(0,0,0,i+1)
            TX_ref_next = T_refT.Nodes[0].FCurve
            TY_ref_next = T_refT.Nodes[1].FCurve
            TZ_ref_next = T_refT.Nodes[2].FCurve
            TX_ref_next.KeyAdd(frame_next, TX_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            TY_ref_next.KeyAdd(frame_next, TY_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            TZ_ref_next.KeyAdd(frame_next, TZ_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RX_ref_next = R_hipT.Nodes[0].FCurve
            RY_ref_next = R_hipT.Nodes[1].FCurve
            RZ_ref_next = R_hipT.Nodes[2].FCurve
            RX_ref_next.KeyAdd(frame_next, RX_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RY_ref_next.KeyAdd(frame_next, RY_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            RZ_ref_next.KeyAdd(frame_next, RZ_ref_next.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
            if is_dyadic:
                TX_ref_nextF = T_refF.Nodes[0].FCurve
                TY_ref_nextF = T_refF.Nodes[1].FCurve
                TZ_ref_nextF = T_refF.Nodes[2].FCurve
                TX_ref_nextF.KeyAdd(frame_next, TX_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
                TY_ref_nextF.KeyAdd(frame_next, TY_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
                TZ_ref_nextF.KeyAdd(frame_next, TZ_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
                RX_ref_nextF = R_hipF.Nodes[0].FCurve
                RY_ref_nextF = R_hipF.Nodes[1].FCurve
                RZ_ref_nextF = R_hipF.Nodes[2].FCurve
                RX_ref_nextF.KeyAdd(frame_next, RX_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
                RY_ref_nextF.KeyAdd(frame_next, RY_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)
                RZ_ref_nextF.KeyAdd(frame_next, RZ_ref_nextF.Evaluate(frame_next), FBInterpolation.kFBInterpolationLinear)

            # the next frame is the first frame, nothing more to process
            if i == -1:
                i = 0
                continue

        ### normalize rotation
        # inversely apply the average rotation to the current one
        rot_matT = FBMatrix()
        rot_newT = FBVector3d()
        target_hipbone.GetMatrix(rot_matT, FBModelTransformationType.kModelRotation, False)
        FBMatrixToRotation(rot_newT, y_rot_mat * rot_matT)
        target_hipbone.SetVector(rot_newT, FBModelTransformationType.kModelRotation, False)
        target_hipbone.Rotation.Key()
        if is_dyadic:
            rot_matF = FBMatrix()
            rot_newF = FBVector3d()
            facing_hipbone.GetMatrix(rot_matF, FBModelTransformationType.kModelRotation, False)
            FBMatrixToRotation(rot_newF, y_rot_mat * rot_matF)
            facing_hipbone.SetVector(rot_newF, FBModelTransformationType.kModelRotation, False)
            facing_hipbone.Rotation.Key()

        ### normalize position
        pos_origT = FBVector3d()
        target_refbone.GetVector(pos_origT, FBModelTransformationType.kModelTranslation, False)
        # subtract the average position
        pos_newT = FBVector4d(pos_origT[0] - pos_acc[0], pos_origT[1] - pos_acc[1], pos_origT[2] - pos_acc[2],0)
        # rotate the position w.r.t the hip rotation from earlier
        pos_new_rotatedT = FBVector4d()
        FBVectorMatrixMult(pos_new_rotatedT, y_rot_mat, pos_newT)
        pos_new_rotatedT = FBVector3d(pos_new_rotatedT[0], pos_new_rotatedT[1], pos_new_rotatedT[2])
        # set the new position
        target_refbone.SetVector(pos_new_rotatedT, FBModelTransformationType.kModelTranslation, False)
        target_refbone.Translation.Key()
        if is_dyadic:
            pos_origF = FBVector3d()
            facing_refbone.GetVector(pos_origF, FBModelTransformationType.kModelTranslation, False)
            pos_newF = FBVector4d(pos_origF[0] - pos_acc[0], pos_origF[1] - pos_acc[1], pos_origF[2] - pos_acc[2],0)
            pos_new_rotatedF = FBVector4d()
            FBVectorMatrixMult(pos_new_rotatedF, y_rot_mat, pos_newF)
            pos_new_rotatedF = FBVector3d(pos_new_rotatedF[0], pos_new_rotatedF[1], pos_new_rotatedF[2])
            facing_refbone.SetVector(pos_new_rotatedF, FBModelTransformationType.kModelTranslation, False)
            facing_refbone.Translation.Key()

        FBPlayerControl().StepForward()
        i += 1
        
    # optimize curves with linear interpolation and unrolling filter to make values continuous
    unroll_filter = FBFilterManager().CreateFilter('Unroll Rotations')
    unroll_filter.Start = FBTime(0,0,0,0)
    unroll_filter.Stop = FBTime(0,0,0,total_frames)
    unroll_filter.Apply(R_hipT, True)
    if is_dyadic:
        unroll_filter.Apply(R_hipF, True)

def export_BVH(output_path, namespace):
    # center the root so translation is baked to 0,0,0 in BVH spec (does not alter the animation data)
    FBPlayerControl().GotoStart()
    FBFindModelByLabelName(namespace + ':body_world').SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelTranslation, False)
    
    # deselect everything
    selectedModels = FBModelList()
    FBGetSelectedModels (selectedModels, None, True)
    for selected in selectedModels:
        selected.Selected = False

    # select the bones we want to export
    objList = FBComponentList()
    FBFindObjectsByName(namespace + ":*", objList, True, False)
    for o in objList:
        o.Selected=True

    # export
    FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
    FBSystem().Scene.Evaluate()
    FBApplication().FileExport(output_path)

NAMESPACE_TARGET = "Target" # the speaker we are normalizing for
NAMESPACE_FACING = "Faced"  # the speaker the target is facing

if FILE_BVH_FACING != "" and not os.path.exists(FILE_BVH_FACING):
    raise FileNotFoundError("The BVH file for the interlocutor being faced could not be found. Tried: \"" + FILE_BVH_FACING + "\".")

# Import BVH
import_BVH(FILE_BVH, TAKE_NAME, NAMESPACE_TARGET)
FBSystem().Scene.Evaluate()
if DYADIC:
    import_BVH(FILE_BVH_FACING, TAKE_NAME, NAMESPACE_FACING)
    FBSystem().Scene.Evaluate()

# Normalize root
normalize_root(NAMESPACE_TARGET, NAMESPACE_FACING, DYADIC, 250)

# Export BVH
export_BVH(FILE_BVH_EXPORTED, NAMESPACE_TARGET)
if DYADIC:
    export_BVH(FILE_BVH_EXPORTED_FACING, NAMESPACE_FACING)
