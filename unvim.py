#!/usr/bin/env python
"""
Displays images from "Broken Sword II: Director's Cut" contained in *.vim
files, themselves being in 2 files: comic.dat and menu_gfx.dat .

Usage:
  unvim.py file
"""
import sys
from struct import unpack, pack
import os.path
import zlib
import pygame
from cStringIO import StringIO

def main():
    infile_name = sys.argv[1]
    base_name, ext = infile_name.rsplit(os.path.extsep, 1)
    base_name = os.path.basename(base_name)
    assert ext == 'vim', ext
    infile = open(infile_name, 'r')
    width, height, packed_data_len = unpack('<HHI', infile.read(8))
    is16, width = bool(width & 0x8000), width & 0x7fff
    data = zlib.decompress(infile.read(packed_data_len))
    if is16:
        # 16bits colors, needs conversion to RGB as pygame doesn't support it.
        fmt = 'RGB'
        new_bitmap = StringIO()
        bitmap = StringIO(data)
        scale = lambda x: pack('BBB', (x >> 8) & 0xf8, (x >> 3) & 0xfc, (x << 3) & 0xf8)
        while True:
            chunk = bitmap.read(2)
            if not chunk:
                break
            new_bitmap.write(scale(unpack('<H', chunk)[0]))
        data = new_bitmap.getvalue()
    else:
        fmt = 'RGBA'
    image = pygame.image.fromstring(data, [width, height], fmt)
    pygame.init()
    screen = pygame.display.set_mode([width, height])
    clock = pygame.time.Clock()
    checkerboard = pygame.Surface([width, height])
    checkerboard.fill((85, 85, 85, 255))
    white = pygame.Surface((5, 5))
    white.fill((170, 170, 170, 255))
    for x in xrange(0, width, 5):
        for y in xrange(x % 10, height, 10):
            checkerboard.blit(white, [x, y])
    screen.blit(checkerboard, [0, 0])
    screen.blit(image, [0, 0])
    pygame.display.flip()
    done = False
    while not done:
        for event in pygame.event.get():
            done = event.type == pygame.QUIT
        clock.tick(10)
    pygame.quit()

if __name__ == '__main__':
    main()
