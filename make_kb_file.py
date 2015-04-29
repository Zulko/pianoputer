#!/usr/bin/env python

import pygame as pg

kb_file = open("my_keyboard.kb", 'w')

pg.init()
screen = pg.display.set_mode((200, 200))
print("Press the keys in the right order. Press Escape to finish.")
while True:
    event = pg.event.wait()
    if event.type is pg.KEYDOWN:
        if event.key == pg.K_ESCAPE:
            break
        else:
            name = pg.key.name(event.key)
            print("Last key pressed: %s" % name)
            kb_file.write(name + '\n')

kb_file.close()
print("Done. you have a new keyboard configuration file: %s" % (kb_file.name))
pg.quit()
