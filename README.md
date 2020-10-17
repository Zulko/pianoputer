# Pianoputer

This repository contains a minimal code to play on your computer keyboard like if it was a piano, an instrument that I call the Pianoputer (yeah I am not very good at names). Here is a [video](https://www.youtube.com/watch?v=z410eauCnHc) of the program in action.

## Installation

To play you first need to install Python, and the Python libraries Numpy, Scipy and Pygame (this command should install them: ``pip install scipy pygame``).

## Play! 

Unzip or clone the project in a folder, and type:

```
python pianoputer.py
```

After a few seconds, a black window will appear, indicating that the program is ready.

## Changing the sound file

You can provide your own sound file with

```
python pianoputer.py --wav my_sound_file.wav
```

If the sound file is in stereo mode, you'll need to use

```
python pianoputer_stereo.py --wav my_sound_file.wav
```

## Changing the keyboard layout

Note that the default keyboard configuration (stored in file `typewriter.kb`) is for AZERTY french keyboards. You can change the configuration so that it matches your keyboard, for instance using the alternative `typewriter_us.kb`:

```
python pianoputer.py --keyboard typewriter_us.kb
```

These `.kb` files simply contain a sequence of key names and are easy to edit. For convenience this repository also provides a `make_kb_file.py` program:
```
python make_kb_file.py
```

This will let you press the keys in the order that you want, and create a new keyboard configuration file, by default `my_keyboard.kb` (just follow the instructions). You can then use the custom keyboard file with:
