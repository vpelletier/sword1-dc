#!/usr/bin/env python
"""
Data extractor for "Broken Sword: Director's Cut"
Tested on a GOG.com install.
Extracts data in pwd. Data might contain paths with nice filenames
(menu_gfx.dat) or numeric names (all others).

Usage:
  extract.py file

file:
  One of the *.dat files from "Broken Sword: Director's Cut" install.
"""
from struct import unpack
from os.path import dirname, isdir
from os import makedirs
import sys
import zlib

def main():
    infile = open(sys.argv[1], 'r')
    magic, entries = unpack('<4sI', infile.read(8))
    if magic == 'HSFS':
        unpackHSFS(infile, entries)
    elif magic == 'RARC':
        unpackRARC(infile, entries)
    elif magic == 'AUFS':
        unpackAUFS(infile, entries)
    else:
        print "Bad magic:", repr(magic)

def unpackHSFS(infile, entries):
    """
    Valid for: bs1dc.dat
    Content: various binary formats, some starting with a 4-bytes format name:
      BACK BM16 FACE FG16 FORE SPR4 SPR8 SPRA
    """
    file_map = []
    for _ in xrange(entries):
        file_map.append(unpack('<IIII', infile.read(16)))
    for ident, offset, length, zip_length in file_map:
        infile.seek(offset)
        open('%08x' % (ident, ), 'w').write(zlib.decompress(infile.read(zip_length)))

def unpackRARC(infile, entries):
    """
    Valid for: menu_gfx.dat
    Content: PNG images
    """
    file_map = []
    for _ in xrange(entries):
        file_map.append(unpack('<64sII', infile.read(72)))
    for name, offset, length in file_map:
        name = name.rstrip('\x00')
        dirs = dirname(name)
        if not isdir(dirs):
            makedirs(dirname(name))
        infile.seek(offset)
        open(name, 'w').write(infile.read(length))

def unpackAUFS(infile, entries):
    """
    Valid for: sfx.dat speech_?.dat
    Content: OGG vorbis
    """
    file_map = []
    for _ in xrange(entries):
        file_map.append(unpack('<III', infile.read(12)))
    for ident, offset, length in file_map:
        infile.seek(offset)
        open('%08x' % (ident, ), 'w').write(infile.read(length))

if __name__ == '__main__':
    main()

