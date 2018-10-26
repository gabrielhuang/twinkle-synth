import numpy as np

def cos_degree(degree):
    return np.cos(np.deg2rad(degree))

def sin_degree(degree):
    return np.sin(np.deg2rad(degree))

def angle_to_xyz(azimuth, elevation, radius=1.):
    x = radius * cos_degree(elevation) * cos_degree(azimuth)
    y = radius * cos_degree(elevation) * sin_degree(azimuth)
    z = radius * sin_degree(elevation)
    return x, y, z

# Sound stuff
def read_frames(wf):
    all_frames = []
    while True:
        frames = wf.readframes(44100)
        if not frames:
            break
        all_frames.append(frames)
    all_frames = ''.join(all_frames)
    print len(all_frames)
    return all_frames


def frames_to_np(frames, dtype=np.int16):  # assume stereo
    input = np.frombuffer(frames, dtype=dtype)
    return input


MAX = 32767
def np_to_frames(np_array):
    output = np_array.clip(-MAX, MAX).astype(np.int16).tostring()
    return output


def to_stereo(left, right):
    return np.vstack((left, right)).T.flatten()


def to_monos(stereo):
    reshaped = stereo.reshape((-1, 2))
    left = reshaped[:, 0].copy()
    right = reshaped[:, 1].copy()
    return left, right


def get_subset(a, start, length):
    if length > len(a[start:]):
        filler = np.zeros(length - len(a[start:]), dtype=a.dtype)
        return np.hstack((a[start:], filler))
    else:
        return a[start:start + length]

def get_subset_wrap(a, start, length):
    idx = np.mod(np.arange(start, start+length), len(a))
    return a[idx]
