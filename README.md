# Pianoputer

This repository contains a minimal code to play on your computer keyboard like if it was a piano, an instrument that I call the Pianoputer (yeah I am not very good at names). Here is a [video](https://www.youtube.com/watch?v=z410eauCnHc) of the program in action.

## Installation

To play you first need to install Python, and the Python libraries Numpy, Scipy and Pygame (this command should install them: ``pip install scipy pygame``).

## Play!

Unzip or clone the project in a folder, and type:

```
python pianoputer.py
```

After a few seconds, a window will appear, indicating that the program is ready.

## Changing the sound file

You can provide your own sound file with

```
python pianoputer.py --wav my_sound_file.wav
```

## Changing the keyboard layout

Note that the default keyboard configuration (stored in file `keyboard_qwerty_43keys.txt`) is for the most commonly used QWERTY keyboards. You can change the configuration so that it matches your keyboard, for instance using the alternative `keyboards/azerty_49keys.txt`:

```
python pianoputer.py -k keyboards/azerty_49keys.txt -w audio_files/bowlStereo_c6.wav
```

These `.txt` files simply contain a sequence of key names and are easy to edit. For convenience this repository also provides a `make_kb_file.py` program:
```
python make_kb_file.py
```

This will let you press the keys in the order that you want, and create a new keyboard configuration file, by default `my_keyboard.kb` (just follow the instructions). You can then use the custom keyboard file with the --keyboard argument

## TODO
- [DONE] add qwerty layout
- [DONE] add image for keyboard
- [DONE] add piano sample for qwerty
- [DONE] add caching
- [DONE] update sample to be c4
- [DONE] have ui show the keyboard image
- [DONE] have ui be the size of the image
- [DONE] confirm that tool works for stereo files too
- [DONE] add clear-cache command
- [DONE] update azerty to be anchored at certain location
- [DONE] update azerty keyboard to show the anchor key
- make installable through pypi
- Fix the azerty bowl sample to be at a c6
- allow non-anchor note to be passed in + write note anchor in UI
- autodetect input file frequency and pitch shift it to the needed start frequency?

## Attributions
- qwerty keyboard images By No machine-readable author provided. Denelson83 assumed (based on copyright claims). - No machine-readable source provided. Own work assumed (based on copyright claims)., CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=508928
- c4 piano sample from https://en.wikipedia.org/wiki/File:Middle_C.mid
