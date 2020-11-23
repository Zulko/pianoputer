#!/usr/bin/env python

from scipy.io import wavfile
import argparse
import numpy as np
import pygame
import warnings
import wave
import librosa
from pathlib import Path
import soundfile
import re
import typing
import os
import shutil

anchor_note_regex = re.compile("[abcdefg]\d$")

DESCRIPTOR_32BIT = 'FLOAT'
BITS_32BIT = 32

def parse_arguments():
    description = ('Use your computer keyboard as a "piano"')

    parser = argparse.ArgumentParser(description=description)
    default_wav_file = 'audio_files/piano_c4.wav'
    parser.add_argument(
        '--wav', '-w',
        metavar='FILE',
        type=str,
        default=default_wav_file,
        help='WAV file (default: {})'.format(default_wav_file))
    # https://github.com/mehrdad-dev/Jami/blob/master/assets/keyboard.jpg
    # qwerty keyboard
    default_keyboard_file = 'keyboards/qwerty_43keys.txt'
    parser.add_argument(
        '--keyboard', '-k',
        metavar='FILE',
        type=argparse.FileType('r'),
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
    tones: typing.List[int],
    anchor_note: str,
    clear_cache: bool,
) -> typing.List[pygame.mixer.Sound]:
    sounds = []
    y, sr = librosa.load(wav_path, sr=sample_rate_hz)
    file_name = os.path.splitext(os.path.basename(wav_path))[0]
    match = anchor_note_regex.search(file_name)
    if not match:
        raise ValueError(
            "Invalid audio file passed in for this keyboard\n"
            "Keyboard requires anchor note {} and the wave file lacks the "
            "required anchor note suffix. Pass in {}_{}.wav".format(
                anchor_note, file_name, anchor_note
            )
        )
    wav_anchor_note = file_name[-2:]
    if wav_anchor_note != anchor_note:
        raise ValueError(
            "Invalid audio file passed in for this keyboard\n"
            "Keyboard requires anchor note {} and the wave passed in {}\n"
            "Pass in {}_{}.wav".format(
                anchor_note, wav_anchor_note, file_name, anchor_note
            )
        )
    folder_path = Path("audio_files/{}".format(file_name))
    if clear_cache and folder_path.exists():
        shutil.rmtree(folder_path)
    if not folder_path.exists():
        print('Generating samples for each key')
        os.mkdir(folder_path)
    for i, tone in enumerate(tones):
        cached_path = 'audio_files/{}/{}.wav'.format(file_name, tone)
        if Path(cached_path).exists():
            print(
                "Loading note {} out of {}".format(i+1, len(tones))
            )
            sound, sr = librosa.load(cached_path, sr=sample_rate_hz)
        else:
            print(
                "Transposing note {} out of {}".format(i+1, len(tones))
            )
            sound = librosa.effects.pitch_shift(y, sr, n_steps=tone)
            soundfile.write(
                cached_path, sound, sample_rate_hz, DESCRIPTOR_32BIT)
        sounds.append(sound)
    sounds = map(pygame.sndarray.make_sound, sounds)
    return sounds

def get_keyboard_info(keyboard_file):
    lines = keyboard_file.read().split('\n')
    keys = []
    anchor_note = ""
    anchor_index = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        match = anchor_note_regex.search(line)
        if match:
            anchor_note = line[-2:]
            line = line[:-3]
            achor_index = i
        keys.append(line)
    if not anchor_note:
        raise ValueError(
            "Invalid keyboard file, one key must have an anchor note written "
            "next to it.\n"
            "For example 'm c4' c4 refers to middle c at 261.6 hz.\n"
            "To learn more about the possible anchor notes look here:\n"
            "https://en.wikipedia.org/wiki/Piano_key_frequencies"
        )
    tones = [i - achor_index for i in range(len(keys))]
    keyboard_img_path = keyboard_file.name[:-3] + 'png'
    try:
        keyboard_img = pygame.image.load(keyboard_img_path)
    except FileNotFoundError:
        keyboard_img = None
    return keys, tones, anchor_note, keyboard_img

def configure_pygame_audio_and_set_ui(
    framerate_hz: int,
    channels: int,
    keyboard_img: typing.Optional['pygame.image']
):
    # audio
    pygame.mixer.init(framerate_hz, BITS_32BIT, channels)

    # ui
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

def play_until_esc_pressed(
    keys: typing.List[str],
    key_sounds: typing.List[pygame.mixer.Sound]
):
    key_sound = dict(zip(keys, sounds))
    is_pressed = {k: False for k in keys}
    playing = True

    while playing:
        event = pygame.event.wait()

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            key = pygame.key.name(event.key)

        if event.type == pygame.KEYDOWN:
            if (key in key_sound.keys()) and (not is_pressed[key]):
                key_sound[key].play(fade_ms=50)
                is_pressed[key] = True

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                playing = False

        elif event.type == pygame.KEYUP and key in key_sound.keys():
            # Stops with 50ms fadeout
            key_sound[key].fadeout(50)
            is_pressed[key] = False

        elif event.type == pygame.QUIT:
            pygame.quit()
            playing = False

    print('Goodbye')

def main():
    args = parse_arguments()

    # Enable warnings from scipy if requested
    if not args.verbose:
        warnings.simplefilter('ignore')

    with wave.open(args.wav, 'rb') as wav_file:
        framerate_hz = wav_file.getframerate()
        channels = wav_file.getnchannels()

    keys, tones, anchor_note, keyboard_img = get_keyboard_info(args.keyboard)
    key_sounds = get_or_create_key_sounds(
        args.wav, framerate_hz, tones, anchor_note, args.clear_cache)
    configure_pygame_audio_and_set_ui(framerate_hz, channels, keyboard_img)
    print(
        'Ready for you to play!\n'
        'Press the keys on your keyboard. '
        'To exit presss ESC or close the pygame window'
    )
    play_until_esc_pressed(keys, key_sounds)


if __name__ == '__main__':
    main()
