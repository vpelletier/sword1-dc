#!/usr/bin/env python
"""
Dump strings out of sword1:dc caption files, along with their identifier.
THere is no magic in those files, so you should check file format before
running this script.
Output is sorted by identifier, not by file order.

Usage:
  dump.py file
"""
import sys
from struct import unpack

def main():
    infile = open(sys.argv[1], 'r')
    read = infile.read
    string_list = []
    append = string_list.append
    while True:
        ident, offset = unpack('<II', read(8))
        if not ident and string_list:
            break
        append((ident, offset))
    for ident, offset in sorted(string_list, key=lambda x: x[0]):
        infile.seek(offset)
        caption = ''
        while '\0' not in caption:
            chunk = read(512)
            if not chunk:
                break
            caption += chunk
        caption = caption[:caption.find('\0')]
        print '%08x' % (ident, ), repr(caption)

if __name__ == '__main__':
    main()
