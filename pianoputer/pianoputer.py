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
import keyboardlayout as kl
from collections import defaultdict

ANCHOR_INDICATOR = ' anchor'
ANCHOR_NOTE_REGEX = re.compile("\s[abcdefg]$")
DESCRIPTION = 'Use your computer keyboard as a "piano"'
DESCRIPTOR_32BIT = 'FLOAT'
BITS_32BIT = 32
SOUND_FADE_MILLISECONDS = 50

AUDIO_ASSET_PREFIX = 'audio_files/'
KEYBOARD_ASSET_PREFIX = 'keyboards/'
CURRENT_WORKING_DIR = Path(__file__).parent.absolute()
ALLOWED_EVENTS = {pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT}

def get_parser() -> argparse.ArgumentParser:
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

    return parser

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

BLACK_INDICES_C_SCALE = [1, 3, 6, 8, 10]
LETTER_KEYS_TO_INDEX = {
    'c': 0,
    'd': 2,
    'e': 4,
    'f': 5,
    'g': 7,
    'a': 9,
    'b': 11
}

def __get_black_key_indices(key_name: str):
    letter_key_index = LETTER_KEYS_TO_INDEX[key_name]
    black_key_indices = set()
    for ind in BLACK_INDICES_C_SCALE:
        new_index = (ind - letter_key_index)
        if new_index < 0:
            new_index += 12
        black_key_indices.add(new_index)
    return black_key_indices

def get_keyboard_info(keyboard_file: str):
    with open(keyboard_file, 'r') as k_file:
        lines = k_file.readlines()
    keys = []
    anchor_index = -1
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        match = ANCHOR_NOTE_REGEX.search(line)
        if match:
            anchor_index = i
            black_key_indices = __get_black_key_indices(line[-1])
            line = line[:match.start(0)]
        keys.append(line)
    if anchor_index == -1:
        raise ValueError(
            "Invalid keyboard file, one key must have an anchor note written "
            "next to it.\n"
            "For example 'm c'.\n"
            "That tells the program that the wav file will be used for key m, "
            "and all other keys will be pitch shifted higher or lower from "
            "that anchor and key colors (black/white) are set by that anchor"
        )
    tones = [i - anchor_index for i in range(len(keys))]
    color_name_to_key_name = defaultdict(list)
    for index, key_name in enumerate(keys):
        if index == anchor_index:
            color_name_to_key_name['cyan'].append(key_name)
            continue
        used_index = (index - anchor_index) % 12
        if used_index in black_key_indices:
            color_name_to_key_name['black'].append(key_name)
            continue
        color_name_to_key_name['white'].append(key_name)
    return keys, tones, color_name_to_key_name

def configure_pygame_audio_and_set_ui(
    framerate_hz: int,
    channels: int,
    keyboard_arg: str,
    color_name_to_key_name: typing.Dict[str, typing.List[str]]
) -> pygame.Surface:
    # ui
    pygame.display.init()
    pygame.display.set_caption('pianoputer')

    # fonts
    pygame.font.init()

    # audio
    pygame.mixer.init(framerate_hz, BITS_32BIT, channels)

    # block events that we don't want
    pygame.event.set_blocked(None)
    pygame.event.set_allowed(list(ALLOWED_EVENTS))

    keyboard_layout = None
    screen_width = 50
    screen_height = 50
    layout_name = None
    if 'qwerty' in keyboard_arg:
        layout_name = 'qwerty'
    elif 'azerty' in keyboard_arg:
        layout_name = 'azerty_laptop'
    if layout_name:
        margin = 4
        key_size = 60
        overrides = {}
        for color_name, key_names in color_name_to_key_name.items():
            override_color = color=pygame.Color(color_name)
            override_key_info = kl.KeyInfo(
                margin=margin,
                color=override_color,
                txt_color=~override_color,
                txt_font=pygame.font.SysFont('Arial', key_size//4),
                txt_padding=(key_size//10, key_size//10),
            )
            for key_name in key_names:
                overrides[key_name] = override_key_info
        grey = pygame.Color('grey')
        keyboard_info = kl.KeyboardInfo(
            position=(0, 0),
            padding=2,
            color=~grey
        )
        key_info = kl.KeyInfo(
            margin=margin,
            color=pygame.Color('grey50'),
            txt_color=~grey,  # invert grey
            txt_font=pygame.font.SysFont('Arial', key_size//4),
            txt_padding=(key_size//6, key_size//10)
        )
        letter_key_size = (key_size, key_size)  # width, height
        keyboard_layout = kl.KeyboardLayout(
            layout_name,
            keyboard_info,
            letter_key_size,
            key_info,
            overrides
        )
        screen_width = keyboard_layout.rect.width
        screen_height = keyboard_layout.rect.height

    screen = pygame.display.set_mode((screen_width, screen_height))
    screen.fill(pygame.Color('black'))
    if keyboard_layout:
        keyboard_layout.draw(screen)
    pygame.display.update()
    return screen


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

def get_audio_data(wav_path: str) -> typing.Tuple:
    audio_data, framerate_hz = soundfile.read(wav_path)
    try:
        channels = len(audio_data[0])
    except TypeError:
        channels = 1
    return audio_data, framerate_hz, channels

def process_args(
    parser: argparse.ArgumentParser,
    args: typing.Optional[typing.List] = None
) -> typing.Tuple:
    if args:
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()

    # Enable warnings from scipy if requested
    if not args.verbose:
        warnings.simplefilter('ignore')

    wav_path = args.wav
    if wav_path.startswith(AUDIO_ASSET_PREFIX):
        wav_path = os.path.join(CURRENT_WORKING_DIR, wav_path)

    keyboard_path = args.keyboard
    if keyboard_path.startswith(KEYBOARD_ASSET_PREFIX):
        keyboard_path = os.path.join(CURRENT_WORKING_DIR, keyboard_path)
    return wav_path, keyboard_path, args.clear_cache

def play_pianoputer():
    parser = get_parser()
    wav_path, keyboard_path, clear_cache = process_args(parser)
    audio_data, framerate_hz, channels = get_audio_data(wav_path)
    keys, tones, color_name_to_key_name = get_keyboard_info(keyboard_path)
    key_sounds = get_or_create_key_sounds(
        wav_path, framerate_hz, channels, tones, clear_cache, keys)

    _screen = configure_pygame_audio_and_set_ui(
        framerate_hz, channels, keyboard_path, color_name_to_key_name)
    print(
        'Ready for you to play!\n'
        'Press the keys on your keyboard. '
        'To exit presss ESC or close the pygame window'
    )
    play_until_user_exits(keys, key_sounds)


if __name__ == '__main__':
    play_pianoputer()
