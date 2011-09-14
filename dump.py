#!/usr/bin/env python
"""
Show bits of file information for some formats found in bs1dc.dat .
Other files contain standard file formats (png/ogg) which are directly
readable.

Usage:
  dump.py file
"""
from struct import unpack, pack
import sys
try:
    import pygame
except ImportError:
    print 'Warning: pygame unavailable, will not display images.'
    def display(*args, **kw):
        pass
else:
    from cStringIO import StringIO
    def display(title, bitmap_list, bpp=16, be=False):
        image_list = []
        image_append = image_list.append
        max_width = max_height = 0
        min_x = min_y = None
        bin_fmt = be and '>H' or '<H'
        scale = lambda x: pack('BBB', (x >> 8) & 0xf8, (x >> 3) & 0xfc, (x << 3) & 0xf8)
        for bitmap, width, height, x, y, palette, alpha in bitmap_list:
            max_width = max(max_width, width + x)
            max_height = max(max_height, height + y)
            if min_x is None:
                min_x = x
                min_y = y
            else:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
            if bpp == 8:
                true_bpp = len(palette[0]) * 8
                bitmap = ''.join(palette[ord(x)] for x in bitmap)
            elif bpp == 4:
                true_bpp = len(palette[0]) * 8
                new_bitmap = []
                append = new_bitmap.append
                for bit_pair in (ord(x) for x in bitmap):
                    append(palette[bit_pair & 0xf])
                    append(palette[bit_pair >> 4])
                bitmap = ''.join(new_bitmap)
            else:
                true_bpp = bpp
            if true_bpp == 16:
                new_bitmap = StringIO()
                bitmap = StringIO(bitmap)
                if alpha is None:
                    fmt = 'RGB'
                else:
                    fmt = 'RGBA'
                    alpha = StringIO(alpha)
                while True:
                    chunk = bitmap.read(2)
                    if not chunk:
                        break
                    data = scale(unpack(bin_fmt, chunk)[0])
                    new_bitmap.write(data)
                    if alpha is not None:
                        new_bitmap.write(alpha.read(1))
                new_bitmap = new_bitmap.getvalue()
                if len(new_bitmap) != width * height * len(fmt):
                    print 'SKIP !'
                    continue
                image_append((
                    pygame.image.fromstring(''.join(new_bitmap), [width, height], fmt),
                    x, y, fmt == 'RGBA'
                ))
            else:
                raise NotImplementedError(true_bpp)
        pygame.init()
        screen = pygame.display.set_mode([max_width - min_x, max_height - min_y])
        pygame.display.set_caption(title)
        clock = pygame.time.Clock()
        done = False
        image_count = len(image_list)
        current_image = 0
        checkerboard = pygame.Surface((max_width - min_x, max_height - min_y))
        checkerboard.fill((85, 85, 85, 255))
        white = pygame.Surface((5, 5))
        white.fill((170, 170, 170, 255))
        for x in xrange(0, max_width - min_x, 5):
            for y in xrange(x % 10, max_height - min_y, 10):
                checkerboard.blit(white, [x, y])
        while not done:
            image, x, y, has_alpha = image_list[current_image]
            current_image = (current_image + 1) % image_count
            if has_alpha:
                screen.blit(checkerboard, [0, 0])
            else:
                screen.fill((0, 0, 0, 255))
            screen.blit(image, [x - min_x, y - min_y])
            pygame.display.flip()
            for event in pygame.event.get():
                done = event.type == pygame.QUIT
            clock.tick(10)
        pygame.quit()

def readPalette(read, entry_count):
    palette = []
    append = palette.append
    for _ in xrange(entry_count):
        append(read(2))
    return palette

def readFilledRows(read, height):
    row_dict = {}
    for row in xrange(height):
        a, offset = unpack('<II', read(8))
        if a:
            row_dict[row] = (a, offset)
    return row_dict

def readRowData(read, seek, base_offset, row_dict, width, height, default_color):
    byte_per_point = len(default_color)
    byte_width = width * byte_per_point
    picture = []
    append = picture.append
    blank = default_color * width
    for row in xrange(height):
        try:
            column, offset = row_dict[row]
        except KeyError:
            data = blank
        else:
            data = ''
            seek(offset + base_offset)
            while len(data) < byte_width:
                offset_type, data_length = unpack('BB', read(2))
                if offset_type == 1:
                    data = data + (default_color * data_length)
                elif offset_type == 2:
                    data = data + read(data_length * byte_per_point)
                else:
                    raise ValueError('Unknown offset type: %r' % (offset_type, ))
        append(data)
    return ''.join(picture)

def readFrameData(read, seek, base_offset, frame_list, has_alpha=False, bpp=8):
    bitmap_list = []
    append = bitmap_list.append
    rshift = {
        8: 0,
        4: 1,
    }[bpp]
    for width, height, x, y, offset, palette in frame_list:
        if not (width or height):
            continue
        if width & 1:
            width += 1
        seek(base_offset + offset)
        bitmap = read(width * height >> rshift)
        if has_alpha:
            alpha = read(width * height >> rshift)
        else:
            alpha = None
        append((bitmap, width, height, x, y, palette, alpha))
    return bitmap_list

def main():
    infile_name = sys.argv[1]
    infile = open(infile_name, 'r')
    image = None
    read = infile.read
    magic = read(8)
    if magic.startswith('BACKG'):
        infile.seek(5)
        width, height, colors = unpack('<HHB', read(5))
        print 'Background, palette with %i colors, %ix%i' % (colors, width, height)
        palette = readPalette(read, colors)
        bitmap = read(width * height)
        display(infile_name, [(bitmap, width, height, 0, 0, palette, None)], bpp=8)
    elif magic.startswith('BM16'):
        infile.seek(4)
        width, height = unpack('<HH', read(4))
        print 'Background, 16bis, %ix%i' % (width, height)
        bitmap = read(width * height * 2)
        display(infile_name, [(bitmap, width, height, 0, 0, None, None)], be=True)
    elif magic.startswith('FACE8 '):
        # all files start with 'FACE8 ', but maybe '8 ' means something else...
        infile.seek(6)
        frames = unpack('<H', read(2))[0]
        print 'Face, palette, 128x192, %i frames' % (frames, )
        palette = readPalette(read, 256)
        display(infile_name, [(read(128 * 192), 128, 192, 0, 0, palette, None) for _ in xrange(frames)], bpp=8)
    elif magic.startswith('FG16'):
        infile.seek(4)
        width, height = unpack('<HH', read(4))
        row_dict = readFilledRows(read, height)
        base_offset = infile.tell()
        print 'Foreground, 16bits, %ix%i, %i filled rows' % (width, height, len(row_dict))
        picture = readRowData(read, infile.seek, base_offset, row_dict, width, height, '\0\0')
        display(infile_name, [(picture, width, height, 0, 0, None, None)], be=True)
    elif magic.startswith('FORE'):
        infile.seek(4)
        width, height = unpack('<HH', read(4))
        default_color = read(1)
        palette = readPalette(read, 256)
        row_dict = readFilledRows(read, height)
        base_offset = infile.tell()
        print 'Foreground, palette, %ix%i, %i filled rows' % (width, height, len(row_dict))
        picture = readRowData(read, infile.seek, base_offset, row_dict, width, height, default_color)
        display(infile_name, [(picture, width, height, 0, 0, palette, None)], bpp=8)
    elif magic.startswith('SPR4\0\0'):
        infile.seek(6)
        framecount = unpack('<H', read(2))[0]
        palette = readPalette(read, 16)
        print 'Sprite, 4-bits palette, %i frames:' % (framecount, )
        frame_list = []
        append = frame_list.append
        for _ in xrange(framecount):
            width, height, x, y, offset = unpack('<HHHHI', read(12))
            print '  %ix%i, display at %ix%i, data at 0x%x' % (width, height, x, y, offset)
            append((width, height, x, y, offset, palette))
        base_offset = infile.tell()
        bitmap_list = readFrameData(read, infile.seek, base_offset, frame_list, bpp=4)
        display(infile_name, bitmap_list, bpp=4)
    elif magic.startswith('SPR8\0\0'):
        infile.seek(6)
        framecount = unpack('<H', read(2))[0]
        palette = readPalette(read, 256)
        print 'Sprite, 8-bits palette, %i frames:' % (framecount, )
        frame_list = []
        append = frame_list.append
        for _ in xrange(framecount):
            width, height, x, y, offset = unpack('<HHHHI', read(12))
            print '  %ix%i, display at %ix%i, data at 0x%x' % (width, height, x, y, offset)
            append((width, height, x, y, offset, palette))
        base_offset = infile.tell()
        bitmap_list = readFrameData(read, infile.seek, base_offset, frame_list)
        display(infile_name, bitmap_list, bpp=8)
    elif magic.startswith('SPRA\0\0'):
        infile.seek(6)
        framecount = unpack('<H', read(2))[0]
        # Skip palette data (one palette per frame !)
        palette_list = [readPalette(read, 256) for _ in xrange(framecount)]
        infile.seek(0x200 * framecount + 8)
        print 'Sprite, 8-bits palette, alpha plane, %i frames:' % (framecount, )
        frame_list = []
        append = frame_list.append
        for palette in palette_list:
            width, height, x, y, offset = unpack('<HHHHI', read(12))
            print '  %ix%i, display at %ix%i, data at 0x%x' % (width, height, x, y, offset)
            append((width, height, x, y, offset, palette))
        base_offset = infile.tell()
        bitmap_list = readFrameData(read, infile.seek, base_offset, frame_list, has_alpha=True)
        display(infile_name, bitmap_list, bpp=8)
    else:
        print "Unknown format"

if __name__ == '__main__':
    main()

