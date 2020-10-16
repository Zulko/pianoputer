from scipy.io import wavfile
import argparse
import numpy as np
from numpy import int16, empty, round, hanning, arange, \
    angle, fft, abs, exp, ndarray, zeros, pi
import pygame
import sys
import warnings
import timeit


def parse_arguments():
    """
    YOU CAN DEFINE THE DEFAULT SETTINGS/OPTIONS
    :return:
    """

    description = ('Use your computer keyboard as a "piano"')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--wav', '-w',
        metavar='FILE',
        type=argparse.FileType('r'),
        # default='bowl.wav',
        default='bowlstereo.wav',
        help='WAV file (default: bowl.wav)')
    parser.add_argument(
        '--keyboard', '-k',
        metavar='FILE',
        type=argparse.FileType('r'),
        default='typewriter.kb',
        help='keyboard file (default: typewriter.kb)')
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='verbose mode')

    return (parser.parse_args(), parser)


def channels(sound_object):
    """
    DETERMINE IF A SOUND OBJECT IS MONO OR STEREO
    RETURN AN INTEGER REPRESENTING THE NUMBER OF CHANNELS (1, 2, 4, 6)
    CHANNEL 4 and 6 ARE NOT IMPLEMENTED YET (NEW FEATURE IN SDL 2.0)

    :param sound_object: numpy.ndarray; Sound samples into an array
    :return: int; return the number of channels
    """
    assert isinstance(sound_object, ndarray), \
        "\nArgument sound_object is not a numpy array type, got %s " % type(sound_object)
    # CHECK MONO/STEREO
    shape = sound_object.shape
    try:
        # MULTI-CHANNELS (2, 4, 6)
        channel = shape[1]
    except IndexError:
        # MOST LIKELY TO BE MONO
        channel = 1

    if channel in (4, 6):
        # SDL 2.0 ONLY
        raise NotImplemented
    return channel

# FLAT_PULSE = pygame.mixer.Sound('..\\Assets\\Flat_pulse.ogg')
# flat_pulse = pygame.sndarray.array(FLAT_PULSE)

ONE_TWELVE     = 1.0 / 12.0
P2_10          = 2 << 10
P2_11          = 2 << 11
P2_12          = 2 << 12
PI2            = 2 * pi
WINDOW_SIZE    = P2_12
H              = P2_10
PHASE          = zeros(WINDOW_SIZE)
HANNING_WINDOW = hanning(WINDOW_SIZE)


# PARSE COMMAND LINE ARGUMENTS
(args, parser) = parse_arguments()

# ENABLE WARNINGS FROM SCIPY IF REQUESTED
if not args.verbose:
    warnings.simplefilter('ignore')


# Notes
#     ----- This function cannot read wav files with 24-bit data.
#
#     Common data types: [1]_
#
#     =====================  ===========  ===========  =============
#          WAV format            Min          Max       NumPy dtype
#     =====================  ===========  ===========  =============
#     32-bit floating-point  -1.0         +1.0         float32
#     32-bit PCM             -2147483648  +2147483647  int32
#     16-bit PCM             -32768       +32767       int16
#     8-bit PCM              0            255          uint8
#     =====================  ===========  ===========  =============
#
#     Note that 8-bit PCM is unsigned.
FREQ, SOUND = wavfile.read(args.wav.name)

# CHECK IF THE SOUND IS MONO OR STEREO
CHANNEL = channels(SOUND)

SOUND_LEN = len(SOUND)

TONES = range(-25, 25)
factor_list = {}
for n in TONES:
    factor_list[n] = (2 ** (n * ONE_TWELVE))


def speedx_mono(input_array, factor):
    """
    SPEEDS UP / SLOWS DOWN A SOUND, BY SOME FACTOR.
    OUTPUT ARRAY ELEMENT SIZES DEPENDS ON THE VARIABLE FACTOR (SEMITONES).

    :param input_array: numpy.ndarray; Sound samples into an array (1d numpy.ndarray type int16)
    :param factor: float;
    :return: Return sound samples (1d numpy.ndarray type int16)
    """
    assert isinstance(input_array, ndarray), \
        "\nArgument input_array is not a numpy array type, got %s " % type(input_array)
    assert isinstance(factor, float), \
        "\nArgument factor is not a float type, got %s " % type(factor)
    indices = round(arange(0, len(input_array), factor))
    indices = indices[indices < len(input_array)].astype(int)
    return input_array[indices]


def speedx_stereo(input_array, factor):
    """
    SPEEDS UP / SLOWS DOWN A SOUND, BY SOME FACTOR.
    OUTPUT ARRAY ELEMENT SIZES VARY IN FUNCTION OF THE VARIABLE FACTOR (SEMITONES).

    :param input_array: numpy.ndarray; Sound samples into an array (2d array type int16)
    :param factor: float; SEMITONES
    :return: Return sound samples (2d numpy.ndarray type int16)
    """
    assert isinstance(input_array, ndarray), \
        "\nArgument input_array is not a numpy array type, got %s " % type(input_array)
    assert isinstance(factor, float), \
        "\nArgument factor is not a float type, got %s " % type(factor)
    indices = round(arange(0, len(input_array), factor))
    indices = indices[indices < len(input_array)].astype(int)
    return input_array[indices, :]

def stretch_mono(snd_array, factor):
    """
    STRETCHES/SHORTENS A SOUND, BY SOME FACTOR.

    SOUND STRETCHING CAN BE DONE USING THE CLASSICAL PHASE VOCODER METHOD.
    YOU FIRST BREAK THE SOUND INTO OVERLAPPING BITS, AND YOU REARRANGE THESE BITS
    SO THAT THEY WILL OVERLAP EVEN MORE (IF YOU WANT TO SHORTEN THE SOUND)
    OR LESS (IF YOU WANT TO STRETCH THE SOUND)

    * COMPATIBLE ONLY WITH MONO SOUND

    :param snd_array: numpy.ndarray; Sound samples into an array (1d array type int16)
    :param factor: float; SEMITONES
    :return: return 1d numpy.ndarray type int16
    """
    assert isinstance(snd_array, ndarray), \
        "\nArgument input_array is not a numpy array type, got %s " % type(snd_array)
    assert isinstance(factor, float), \
        "\nArgument factor is not a float type, got %s " % type(factor)

    """ Stretches/shortens a SOUND, by some factor. """
    phase = PHASE.copy()
    result = zeros(int(SOUND_LEN / factor + WINDOW_SIZE))

    for i in arange(0, SOUND_LEN - (WINDOW_SIZE + H), H*factor):
        i = int(i)
        # TWO POTENTIALLY OVERLAPPING SUBARRAY
        a1 = snd_array[i: i + WINDOW_SIZE]
        a2 = snd_array[i + H: i + WINDOW_SIZE + H]

        # The spectra of these arrays
        s1 = fft.fft(HANNING_WINDOW * a1)
        s2 = fft.fft(HANNING_WINDOW * a2)

        # REPHASE ALL FREQUENCIES
        phase = (phase + angle(s2/s1)) % PI2

        a2_rephased = fft.ifft(abs(s2)*exp(1j*phase))
        i2 = int(i/factor)
        result[i2: i2 + WINDOW_SIZE] += HANNING_WINDOW*a2_rephased.real

    # NORMALIZE (16BIT)
    result = (P2_11 * result/result.max())

    return result.astype('int16')


def stretch_stereo(snd_array, factor):
    """
    STRETCHES/SHORTENS A SOUND, BY SOME FACTOR.

    SOUND STRETCHING CAN BE DONE USING THE CLASSICAL PHASE VOCODER METHOD.
    YOU FIRST BREAK THE SOUND INTO OVERLAPPING BITS, AND YOU REARRANGE THESE BITS
    SO THAT THEY WILL OVERLAP EVEN MORE (IF YOU WANT TO SHORTEN THE SOUND)
    OR LESS (IF YOU WANT TO STRETCH THE SOUND)

    * COMPATIBLE ONLY FOR STEREO SOUNDS:
    IN STEREOPHONIC SOUND MORE CHANNELS ARE USED (TYPICALLY TWO).
    YOU CAN USE TWO DIFFERENT CHANNELS AND MAKE ONE FEED ONE SPEAKER
    AND THE SECOND CHANNEL FEED A SECOND SPEAKER (WHICH IS THE MOST COMMON STEREO SETUP).
    THIS IS USED TO CREATE DIRECTIONALITY, PERSPECTIVE, SPACE.
    IF YOU’VE EVER LOOKED AT THE WAVEFORM OF A STEREO AUDIO FILE WITHIN A DIGITAL AUDIO WORKSTATION (DAW),
    YOU’VE LIKELY NOTICED THAT THERE ARE TWO WAVEFORMS APART OF THE FILE.
    EACH WAVEFORM REPRESENTS A SINGLE CHANNEL OF AUDIO.

    :param snd_array: numpy.ndarray; Sound samples into an array (2d array type int16)
    :param factor: float; SEMITONES
    :return: return a 2d numpy.ndarray type int16
    """

    assert isinstance(snd_array, ndarray), \
        "\nArgument input_array is not a numpy array type, got %s " % type(snd_array)
    # CHECK CHANNELS
    assert snd_array.shape[1] == 2, \
        "\nArgument input_array is not a valid SOUND sample data," \
        " expecting array shape (w, 2) got (%s, %s)" % snd_array.shape
    assert isinstance(factor, float), \
        "\nArgument factor is not a float type, got %s " % type(factor)

    result = zeros((int(SOUND_LEN / factor + WINDOW_SIZE), 2))
    phase1 = PHASE.copy()
    phase2 = PHASE.copy()

    for i in arange(0, SOUND_LEN - (WINDOW_SIZE + H), H * factor):
        i = int(i)
        # EXTRACT CHANNEL 1 & 2 SECTION (I: I + WINDOW_SIZE)
        a1_ch1 = snd_array[i: i + WINDOW_SIZE, 0]
        a1_ch2 = snd_array[i: i + WINDOW_SIZE, 1]
        # COMPUTE THE ONE-DIMENSIONAL DISCRETE FOURIER
        # TRANSFORM FOR CHANNEL 1 & 2 SECTION (I: I + WINDOW_SIZE)
        s1  = fft.fft(HANNING_WINDOW * a1_ch1)
        s11 = fft.fft(HANNING_WINDOW * a1_ch2)

        # EXTRACT CHANNEL 1 & 2 SECTION (i + H: i + WINDOW_SIZE + H)
        a2_ch1 = snd_array[i + H: i + WINDOW_SIZE + H, 0]
        a2_ch2 = snd_array[i + H: i + WINDOW_SIZE + H, 1]
        # COMPUTE THE ONE-DIMENSIONAL DISCRETE FOURIER
        # TRANSFORM FOR CHANNEL 1 & 2 SECTION (I + H: I + WINDOW_SIZE + H)
        s2  = fft.fft(HANNING_WINDOW * a2_ch1)
        s22 = fft.fft(HANNING_WINDOW * a2_ch2)

        phase1 = (phase1 + angle(s2 / s1)) % PI2
        phase2 = (phase2 + angle(s22 / s11)) % PI2

        a2_rephased  = fft.ifft(abs(s2) * exp(1j * phase1))
        a22_rephased = fft.ifft(abs(s22) * exp(1j * phase2))

        i2 = int(i / factor)

        result[i2: i2 + WINDOW_SIZE, 0] += HANNING_WINDOW * a2_rephased.real
        result[i2: i2 + WINDOW_SIZE, 1] += HANNING_WINDOW * a22_rephased.real

    # NORMALIZE (16BIT)
    result = (P2_12 * result / result.max())

    return result.astype(int16)


def pitchshift(snd_array, n):
    """
    PITCH-SHIFTING IS EASY ONCE YOU HAVE SOUND STRETCHING.
    IF YOU WANT A HIGHER PITCH, YOU FIRST STRETCH THE SOUND WHILE CONSERVING THE PITCH,
    THEN YOU SPEED UP THE RESULT, SUCH THAT THE FINAL SOUND HAS THE SAME DURATION AS
    THE INITIAL ONE, BUT A HIGHER PITCH DUE TO THE SPEED CHANGE.

    :param snd_array: numpy.ndarray; Sound samples into an array (2d array type int16)
    :param n: float; SEMITONES
    :return: return a numpy.ndarray that can be converted into a pygame.sound object
    """

    """ CHANGES THE PITCH OF A SOUND BY ``N`` SEMITONES. """
    assert isinstance(snd_array, ndarray), \
        "\nArgument input_array is not a numpy array type, got %s " % type(snd_array)
    assert isinstance(n, int), \
        "\nArgument n is not a int type, got %s " % type(n)

    # SELECT THE CORRECT ALGORITHM ACCORDING TO THE
    # SOUND TRACKS NUMBER (MON OR STEREO)
    if CHANNEL == 2:
        stretched = stretch_stereo(snd_array, 1.0/factor_list[n])
        return speedx_stereo(stretched[WINDOW_SIZE:], factor_list[n])
    else:
        stretched = stretch_mono(snd_array, 1.0/factor_list[n])
        return speedx_mono(stretched[WINDOW_SIZE:], factor_list[n])


def main():

    sys.stdout.write('Transponding SOUND file... ')
    sys.stdout.flush()
    transposed_sounds = [pitchshift(SOUND, n) for n in TONES]
    print('DONE')

    # So flexible ;)
    # The channels argument is used to specify whether to use mono or stereo.
    # 1 for mono and 2 for stereo.
    # New in pygame 2: The number of channels can also be 4 or 6.
    # Some platforms require the pygame.mixer pygame module for loading and playing
    # sounds module to be initialized after the display modules have initialized.
    # The top level pygame.init() takes care of this automatically, but cannot pass
    # any arguments to the mixer init. To solve this, mixer has a function pygame.mixer.pre_init()
    # to set the proper defaults before the toplevel init is used.

    # The pygame.mixer.init() function takes several optional arguments to control
    # the playback rate and sample size. Pygame will default to reasonable values,
    # but pygame cannot perform Sound ressampling, so the mixer should be initialized
    # to match the values of your audio resources (This is why we are
    # using FREQ, SOUND = wavfile.read(args.wav.name) to extract the sample rate (FREQ)
    pygame.mixer.init(frequency=FREQ, size=-16, channels=CHANNEL, buffer=2048)

    pygame.display.set_mode((250, 250))

    keys = args.keyboard.read().split('\n')

    # CREATE A NEW PLAYABLE SOUND OBJECT FROM AN ARRAY.
    # THE MIXER MODULE MUST BE INITIALIZED AND THE ARRAY FORMAT MUST BE SIMILAR TO THE MIXER AUDIO FORMAT.
    sounds = map(pygame.sndarray.make_sound, transposed_sounds)

    key_sound = dict(zip(keys, sounds))
    is_playing = {k: False for k in keys}

    # todo if the window lost focus cant hear the SOUND
    while True:

        event = pygame.event.wait()

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            key = pygame.key.name(event.key)

        if event.type == pygame.KEYDOWN:
            if (key in key_sound.keys()) and (not is_playing[key]):
                key_sound[key].play(fade_ms=50)
                is_playing[key] = True

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                raise KeyboardInterrupt

        elif event.type == pygame.KEYUP and key in key_sound.keys():
            # Stops with 50ms fadeout
            key_sound[key].fadeout(50)
            is_playing[key] = False


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Goodbye')
