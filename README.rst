This repository contains a minimal code to play on your computer keyboard like if it was a piano, an instrument that I call the Pianoputer (yeah I am not very good at names).

Here is a video_ of the program in action

To play you first need to install Python, and the Python libraries Numpy, Scipy and Pygame. Agreed, the dependencies are a little heavy.

Then you just unzip everything in a folder and run this line:

    python pianoputer.py

Note that the keyboard configuration (stored in the file `typewriter.kb`) is for AZERTY french keyboards. You can change the configuration so that it matches your keyboard. An easy way to do this is to run

    python make_kb_file.py

This will let you press the keys in the order that you want, and create a new keyboard configuration file (just follow the instructions).

Enjoy !

.. _video : https://www.youtube.com/watch?v=z410eauCnHc
