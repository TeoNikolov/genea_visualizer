import bpy
import math
import numpy as np

def read_audio_strided(audio, stride, start, stop):
    rate = audio.getframerate()
    if start < 0: start = 0 # seconds
    if stop  < 0: stop  = audio.getnframes() / rate # seconds
    stop     = math.floor(stop * rate)     # samples
    start    = math.floor(start * rate)    # samples
    stride   = math.floor(stride * rate)   # samples
    if start > audio.getnframes() - 1: start = audio.getnframes() - 1
    if stop  > audio.getnframes(): stop  = audio.getnframes()
    duration = stop - start # samples

    data = []
    sample_count = math.ceil(duration / stride) # samples
    positions = [start + stride * i for i in range(sample_count)]
    for p in positions:
        if p >= audio.getnframes():
            break
        audio.setpos(p)
        sample = np.frombuffer(audio.readframes(1), dtype=np.int16)[0]
        data.append(sample)
    return data

def get_volume(audio, time):
    volume = -1
    time_range = 0.01 # 220 samples (110 before, 110 after)
    stride = 0.001 # 22 samples
    samples = read_audio_strided(audio, stride, time - time_range, time + time_range)
    samples = [abs(x) for x in samples] # absolute
    volume = max(samples)
    return volume

def get_volume_strided(audio, stride, start, stop):
    if start < 0: start = 0
    if stop  < 0: stop = audio.getnframes() / audio.getframerate()
    times = []
    v = start
    i = 0
    while v < stop:
        v = start + stride * i
        times.append(v)
        i += 1
    volumes = [get_volume(audio, t) for t in times]
    return volumes

def smooth_kernel(data, offset=5):
    out_data = []
    for i in range(len(data)):
        start = max(0, i - offset)
        stop = min(len(data), i + offset + 1)
        out_data.append(data[i])
        for j in range(start, stop):
            if data[j] > 0:
                out_data[-1] = 1
                break
    return out_data