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

def parse_arguments():
    description = ('Use your computer keyboard as a "piano"')

    parser = argparse.ArgumentParser(description=description)
    default_wav_file = 'audio_files/piano_c4.wav'
    parser.add_argument(
        '--wav', '-w',
        metavar='FILE',
        type=argparse.FileType('r'),
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

    return (parser.parse_args(), parser)

def transpose_sounds(
    wav_path: str,
    sample_rate_hz: int,
    tones: typing.List[int],
    anchor_note: str,
    clear_cache: bool,
):
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
                cached_path, sound, sample_rate_hz, 'FLOAT')
        sounds.append(sound)
    return sounds

def get_config_info(keyboard_file):
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


def main():
    # Parse command line arguments
    (args, parser) = parse_arguments()

    # Enable warnings from scipy if requested
    if not args.verbose:
        warnings.simplefilter('ignore')

    # TODO change this to std lib
    fps, sound = wavfile.read(args.wav.name)
    keys, tones, anchor_note, keyboard_img = get_config_info(args.keyboard)

    print('Generating samples for each key')
    transposed_sounds = transpose_sounds(
        args.wav.name, fps, tones, anchor_note, args.clear_cache)
    print('DONE')

    # So flexible ;)
    # TODO get channels
    pygame.mixer.init(fps, 32, 1, 2048)
    # For the focus
    BLACK = (0, 0, 0)
    width = 50
    height = 50
    if keyboard_img:
        rect = keyboard_img.get_rect()
        width = rect.width
        height = rect.height
        rect.center = width//2, height//2
    screen = pygame.display.set_mode((width, height))
    screen.fill(BLACK)
    if keyboard_img:
        screen.blit(keyboard_img, rect)
    pygame.display.update()
    # load image
    # img.convert()
    # rect = img.get_rect()
    # rect.center = w//2, h//2

    sounds = map(pygame.sndarray.make_sound, transposed_sounds)
    key_sound = dict(zip(keys, sounds))
    is_playing = {k: False for k in keys}

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
