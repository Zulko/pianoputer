import os
import typing
import unittest

import pianoputer.pianoputer as pp
import pygame


class PianoPuter(unittest.TestCase):
    sample_images_folder = "pianoputer/keyboards/"

    def test_writes_sample_keyboards_to_images(self):
        keyboards = [
            'keyboards/azerty_typewriter.txt', 'keyboards/qwerty_piano.txt']
        for keyboard in keyboards:
            parser = pp.get_parser()
            args = ['-k', keyboard]
            wav_path, keyboard_path, clear_cache = pp.process_args(parser, args)
            audio_data, framerate_hz, channels = pp.get_audio_data(wav_path)
            results = pp.get_keyboard_info(
                keyboard_path)
            _keys, _tones, color_name_to_key, key_color, key_txt_color = results

            screen, _keyboard_graphic = pp.configure_pygame_audio_and_set_ui(
                framerate_hz,
                channels,
                keyboard_path,
                color_name_to_key,
                key_color,
                key_txt_color
            )

            _, file_name_with_ext = os.path.split(keyboard)
            file_name, file_extension = os.path.splitext(file_name_with_ext)
            pygame.image.save(
                screen, self.sample_images_folder + "{}.jpg".format(file_name))
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
