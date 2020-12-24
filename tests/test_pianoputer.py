import os
import shutil
import typing
import unittest
from unittest.mock import patch

import pygame

import pianoputer.pianoputer as pp


class PianoPuter(unittest.TestCase):
    sample_images_folder = "pianoputer/keyboards/"

    def tearDown(self):
        pygame.quit()

    def test_works_with_different_channels(self):
        audio_files = [
            "piano-c4_1channel.wav",
            "piano-c4_2channel.wav",
            "piano-c4_4channel.wav",
        ]

        def get_quit():
            return [pygame.event.Event(pygame.QUIT)]

        for audio_file in audio_files:
            with patch("pygame.event.get", side_effect=get_quit) as m_event_get:
                audio_file_path = os.path.join(os.path.dirname(__file__), audio_file)
                pp.play_pianoputer(["-w", audio_file_path])
            file_name, file_extension = os.path.splitext(audio_file)
            folder_path = os.path.join(os.path.dirname(__file__), file_name)
            shutil.rmtree(folder_path)

    def test_writes_sample_keyboards_to_images(self):
        keyboards = ["keyboards/azerty_typewriter.txt", "keyboards/qwerty_piano.txt"]
        for keyboard in keyboards:
            parser = pp.get_parser()
            args = ["-k", keyboard]
            wav_path, keyboard_path, clear_cache = pp.process_args(parser, args)
            audio_data, framerate_hz, channels = pp.get_audio_data(wav_path)
            results = pp.get_keyboard_info(keyboard_path)
            _keys, _tones, color_name_to_key, key_color, key_txt_color = results

            screen, _keyboard_graphic = pp.configure_pygame_audio_and_set_ui(
                framerate_hz,
                channels,
                keyboard_path,
                color_name_to_key,
                key_color,
                key_txt_color,
            )

            _, file_name_with_ext = os.path.split(keyboard)
            file_name, file_extension = os.path.splitext(file_name_with_ext)
            pygame.image.save(
                screen, self.sample_images_folder + "{}.jpg".format(file_name)
            )


if __name__ == "__main__":
    unittest.main()
