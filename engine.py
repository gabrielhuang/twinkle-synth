import pyaudio
import numpy as np
from collections import OrderedDict
import utils


class MasterPlayer(object):
    def __init__(self, volume=1., samplesPerSecond=44100):
        self.p = pyaudio.PyAudio()
        self.volume = volume
        self.samplesPerSecond = samplesPerSecond
        self.individual_callbacks = OrderedDict()
        self.volumes = {}

    def __del__(self):
        self.p.terminate()

    def play(self):

        self.offset = 0
        def callback(in_data, frame_count, time_info, status):
            total_stereo = np.zeros((frame_count*2))
            time = self.offset / float(self.samplesPerSecond)

            for ic in self.individual_callbacks:
                left, right = ic(self.offset, time, frame_count)
                if left is None:  # dead voice
                    continue
                stereo = utils.to_stereo(left, right)
                # Accumulate
                total_stereo += stereo * self.volumes[ic]

            self.offset += frame_count
            output = utils.np_to_frames(total_stereo * self.volume)
            return (output, pyaudio.paContinue)

        self.stream = self.p.open(format=self.p.get_format_from_width(2),
                channels=2,
                rate=self.samplesPerSecond,
                output=True,
                stream_callback=callback)
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def register(self, callback):
        self.individual_callbacks[callback] = {}
        self.volumes[callback] = 1.

    def unregister(self, callback):
        if callback in self.individual_callbacks:
            del self.individual_callbacks[callback]
            del self.volumes[callback]

    def set_volume(self, callback, volume):
        self.volumes[callback] = volume

MAXVOLUME = 32767.


def sawtooth(x):
    return np.mod(x / (2*np.pi), 1.)

class ADSR(object):
    def __init__(self, a=0.01, d=0.1, s=0.8, r=0.5, mode='linear'):
        self.a = a
        self.d = d
        self.s = s
        self.r = r
        assert mode == 'linear'

    def get_envelope_pressed(self, delta):
        '''
        :param delta: time after pressed
        :return: envelope (between 0 and 1)
        '''
        delta = delta.astype(float)
        #assert delta>0.
        envelope = np.zeros(len(delta))
        # attack
        attack = delta < self.a
        envelope[attack] = delta[attack] / self.a
        # decay
        decay = (delta < self.a + self.d) & (delta >= self.a)
        envelope[decay] = 1 - (1 - self.s) * (delta[decay] - self.a) / self.d
        # sustain
        sustain = (delta >= self.a + self.d)
        envelope[sustain] = self.s

        return envelope

    def get_envelope_released(self, delta):
        '''
        :param delta: time after released
        :return: envelope (between 0 and 1)
        '''
        delta = delta.astype(float)
        envelope = np.zeros(len(delta))

        # release
        release = delta < self.r
        envelope[release] = self.s * (self.r - delta[release]) / self.r

        # dead
        dead = delta >= self.r
        all_dead = np.all(dead)

        return envelope, all_dead


class SineWavePlayer(object):
    def __init__(self, freq, samplerate, adsr, motherwave=None):
        self.freq = freq
        self.samplerate = samplerate
        self.pressed = False
        self.volume = 0.3
        #self.wave = np.sin
        if motherwave is None:
            motherwave = sawtooth()
        self.wave = motherwave
        self.adsr = adsr
        self.dead = True

    def __call__(self, offset, time, frame_count):

        # Find out which state we are in
        # Dead/NewPress/Pressed/NewRelease/Released/Dead
        if self.pressed:
            if self.new_press:
                # Initialize phase to prevent clicking
                self.onset = time
                self.new_press = False
            # Relative time after press
            time_after_press = (time + np.arange(frame_count, dtype=float) / self.samplerate - self.onset)

            left = self.volume * MAXVOLUME * self.wave(time_after_press * 2*np.pi * self.freq)
            envelope = self.adsr.get_envelope_pressed(time_after_press)
            left *= envelope
            right = left
        elif not self.dead:
            if self.new_release:
                self.new_release = False
                self.release_time = time
            # Relative time after release
            time_after_press = (time + np.arange(frame_count, dtype=float) / self.samplerate - self.onset)
            time_after_release = (time + np.arange(frame_count, dtype=float) / self.samplerate - self.release_time)

            left = self.volume * MAXVOLUME * self.wave(time_after_press * 2*np.pi * self.freq)
            envelope, self.dead = self.adsr.get_envelope_released(time_after_release)
            left *= envelope
            right = left
        else:
            left = right = None
        return left, right

    def press(self):
        self.pressed = True
        self.new_press = True
        self.dead = False

    def release(self):
        self.pressed = False
        self.new_release = True


def note_to_freq(note):
    reference_a = 45
    return np.exp(np.log(440) + (note - reference_a) / 12. * np.log(2))


class NaivePoly(object):
    def __init__(self, octaves, samplerate, adsr, motherwave):
        self.voices = []
        self.octaves = octaves
        for note in xrange(self.octaves*12):
            # Compute frequency -> 440hz is note 45
            freq = note_to_freq(note)
            # Initialize voice
            self.voices.append(SineWavePlayer(freq, samplerate, adsr, motherwave))
            print 'note {} freq {}'.format(note, freq)

    def register(self, master):
        for voice in self.voices:
            master.register(voice)

    def unregister(self, master):
        for voice in self.voices:
            master.unregister(voice)

    def press(self, key):
        self.voices[key].press()

    def release(self, key):
        self.voices[key].release()
