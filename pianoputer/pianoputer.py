#!/usr/bin/env python

import argparse
import pygame
import warnings
import librosa
from pathlib import Path
import soundfile
import re
import typing
import os
import shutil
import numpy

ANCHOR_INDICATOR = ' anchor'
ANCHOR_NOTE_REGEX = re.compile("[abcdefg]\d$")
DESCRIPTION = 'Use your computer keyboard as a "piano"'
DESCRIPTOR_32BIT = 'FLOAT'
BITS_32BIT = 32
SOUND_FADE_MILLISECONDS = 50

AUDIO_ASSET_PREFIX = 'audio_files/'
KEYBOARD_ASSET_PREFIX = 'keyboards/'
CURRENT_WORKING_DIR = Path(__file__).parent.absolute()
ALLOWED_EVENTS = {pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT}

def parse_arguments():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    default_wav_file = 'audio_files/piano_c4.wav'
    parser.add_argument(
        '--wav', '-w',
        metavar='FILE',
        type=str,
        default=default_wav_file,
        help='WAV file (default: {})'.format(default_wav_file))
    default_keyboard_file = 'keyboards/qwerty_piano.txt'
    parser.add_argument(
        '--keyboard', '-k',
        metavar='FILE',
        type=str,
        default=default_keyboard_file,
        help='keyboard file (default: {})'.format(default_keyboard_file))
    parser.add_argument(
        '--clear-cache', '-c',
        default=False,
        action='store_true',
        help='deletes stored transposed audio files and recalculates them')
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='verbose mode')

    return parser.parse_args()

def get_or_create_key_sounds(
    wav_path: str,
    sample_rate_hz: int,
    channels: int,
    tones: typing.List[int],
    clear_cache: bool,
    keys: typing.List[str]
) -> typing.Generator[pygame.mixer.Sound, None, None]:
    sounds = []
    y, sr = librosa.load(wav_path, sr=sample_rate_hz, mono=channels==1)
    file_name = os.path.splitext(os.path.basename(wav_path))[0]
    match = ANCHOR_NOTE_REGEX.search(file_name)
    if not match:
        raise ValueError(
            "Invalid audio file passed in for this keyboard\n"
            "The wav file must have an anchor note suffix, "
            "like _a2.wav, _c3.wav etc.\n"
            "Add the required anchor note suffix to your wave file".format(
                anchor_note, file_name, anchor_note
            )
        )
    folder_containing_wav = Path(wav_path).parent.absolute()
    cache_folder_path = Path(folder_containing_wav, file_name)
    if clear_cache and cache_folder_path.exists():
        shutil.rmtree(cache_folder_path)
    if not cache_folder_path.exists():
        print('Generating samples for each key')
        os.mkdir(cache_folder_path)
    for i, tone in enumerate(tones):
        cached_path = Path(cache_folder_path, '{}.wav'.format(tone))
        if Path(cached_path).exists():
            print(
                "Loading note {} out of {} for key {}".format(
                    i+1,
                    len(tones),
                    keys[i]
                )
            )
            sound, sr = librosa.load(
                cached_path, sr=sample_rate_hz, mono=channels==1)
            if channels == 2:
                # the shape must be [length, 2]
                sound = numpy.transpose(sound)
        else:
            print(
                "Transposing note {} out of {} for key {}".format(
                    i+1,
                    len(tones),
                    keys[i]
                )
            )
            if channels == 1:
                sound = librosa.effects.pitch_shift(y, sr, n_steps=tone)
            else:
                left = librosa.effects.pitch_shift(y[0], sr, n_steps=tone)
                right = librosa.effects.pitch_shift(y[1], sr, n_steps=tone)
                sound = numpy.ascontiguousarray(numpy.vstack((left, right)).T)
            soundfile.write(
                cached_path, sound, sample_rate_hz, DESCRIPTOR_32BIT)
        sounds.append(sound)
    sounds = map(pygame.sndarray.make_sound, sounds)
    return sounds

def get_keyboard_info(keyboard_file):
    with open(keyboard_file, 'r') as k_file:
        lines = k_file.readlines()
    keys = []
    anchor_note = ""
    anchor_index = -1
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            anchor_index = line.index(ANCHOR_INDICATOR)
            line = line[:anchor_index]
            achor_index = i
        except ValueError:
            pass
        keys.append(line)
    if anchor_index == -1:
        raise ValueError(
            "Invalid keyboard file, one key must have an anchor note written "
            "next to it.\n"
            "For example 'm anchor'.\n"
            "That tells the program that the wav file will be used for key m, "
            "and all other keys will be pitch shifted higher or lower from "
            "that anchor"
        )
    tones = [i - achor_index for i in range(len(keys))]
    keyboard_img_path = keyboard_file[:-3] + 'png'
    try:
        keyboard_img = pygame.image.load(keyboard_img_path)
    except FileNotFoundError:
        keyboard_img = None
    return keys, tones, keyboard_img

def configure_pygame_audio_and_set_ui(
    framerate_hz: int,
    channels: int,
    keyboard_img: typing.Optional['pygame.image']
):
    # audio
    pygame.mixer.init(framerate_hz, BITS_32BIT, channels)

    # ui
    pygame.display.init()

    # block events that we don't want
    pygame.event.set_blocked(None)
    pygame.event.set_allowed(list(ALLOWED_EVENTS))


    BLACK = (0, 0, 0)
    width = 50
    height = 50
    if keyboard_img:
        rect = keyboard_img.get_rect()
        width = rect.width
        height = rect.height
        rect.center = width//2, height//2
    # For the focus
    screen = pygame.display.set_mode((width, height))
    screen.fill(BLACK)
    if keyboard_img:
        screen.blit(keyboard_img, rect)
    pygame.display.update()


def play_until_user_exits(
    keys: typing.List[str],
    key_sounds: typing.List[pygame.mixer.Sound]
):
    sound_by_key = dict(zip(keys, key_sounds))
    playing = True

    while playing:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                playing = False
                break
            elif event.key == pygame.K_ESCAPE:
                playing = False
                break

            key = pygame.key.name(event.key)
            try:
                sound = sound_by_key[key]
            except KeyError:
                continue

            if event.type == pygame.KEYDOWN:
                sound.stop()
                sound.play(fade_ms=SOUND_FADE_MILLISECONDS)
            elif event.type == pygame.KEYUP:
                sound.fadeout(SOUND_FADE_MILLISECONDS)

    pygame.quit()
    print('Goodbye')

def play_pianoputer():
    args = parse_arguments()

    # Enable warnings from scipy if requested
    if not args.verbose:
        warnings.simplefilter('ignore')

    wav_path = args.wav
    if wav_path.startswith(AUDIO_ASSET_PREFIX):
        wav_path = os.path.join(CURRENT_WORKING_DIR, wav_path)
    audio_data, framerate_hz = soundfile.read(wav_path)
    try:
        channels = len(audio_data[0])
    except TypeError:
        channels = 1

    keyboard_path = args.keyboard
    if keyboard_path.startswith(KEYBOARD_ASSET_PREFIX):
        keyboard_path = os.path.join(CURRENT_WORKING_DIR, keyboard_path)
    keys, tones, keyboard_img = get_keyboard_info(keyboard_path)

    key_sounds = get_or_create_key_sounds(
        wav_path, framerate_hz, channels, tones, args.clear_cache, keys)

    configure_pygame_audio_and_set_ui(framerate_hz, channels, keyboard_img)
    print(
        'Ready for you to play!\n'
        'Press the keys on your keyboard. '
        'To exit presss ESC or close the pygame window'
    )
    play_until_user_exits(keys, key_sounds)


if __name__ == '__main__':
    play_pianoputer()
