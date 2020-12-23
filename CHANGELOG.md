## 2.0.1
- Fixes bug where audio files could not be loaded because mixer.init was not
  allowing the data to be modified to suit the hardware needs
- 1, 2, and 4 channel wave files now supported

## 2.0.0
- Add qwerty keyboard layout and defaults to using it
- Adds images for the qwery and azerty keyboards, cyan is the anchor key
- Displays the keyboard layout images when the program is running
- Quits the program if the pygame window is closed
- Adds caching of transposed audio files on the user's hard drive
- Updates bowl samples to be c6 note
- Adds a clear-cache command, invoke it with -c
- Breaking: Updates keyboard file format to end in txt and require an anchor note or key
- Changes pitch shifting to use librosa, this works for mono and stereo files
- Adds pypi installation with setup.py

## 1.0.0
- https://github.com/Zulko/pianoputer/commit/11c25b342a43af3fb367a4cda515e87a7c9a04f1
