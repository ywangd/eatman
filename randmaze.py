#!/usr/bin/env python
'''
Generate a random maze for EatMan.
'''
import sys, random
from pprint import pprint
import pygame
from pygame.locals import *
import eatman

UP = 'u'
LEFT = 'l'
DOWN = 'd'
RIGHT = 'r'

DISPLAYSURF = None
BASICFONT = None

xp_isolate = {}
xp_visited = {}
xp_stack = []

# how many cross points for each type, i.e. only one other cross point
# is linked to them, 2 cross points lined to them etc.
xp_nlinks = {0:0, 1:0, 2:0, 3:0, 4:0}


def add_to_isolate((r, c)):
    global xp_isolate, xp_visited, xp_nlinks
    key = (r, c)
    if xp_visited.has_key(key):
        del xp_visited[key]
    xp_isolate[(r,c)] = []
    xp_nlinks[0] += 1

def add_to_visited((r, c), neighbours=[]):
    global xp_isolate, xp_visited, xp_nlinks
    key = (r, c)
    if xp_isolate.has_key(key):
        del xp_isolate[key]

    if xp_visited.has_key(key):
        pass
    else:
        xp_visited[key] = neighbours

def push_to_stack(coords, from_coords):
    for ii in range(len(xp_stack)-1,-1,-1):
        pack = xp_stack[ii]
        if pack[0] == coords:
            xp_stack.remove(pack)

    xp_stack.append([coords, from_coords])

def get_random_direction(coords, data):
    row, col = coords
    nrows = len(data)
    ncols = len(data[0])

    pdir = {
            UP: (row-2, col), 
            LEFT: (row, col-2), 
            DOWN: (row+2, col), 
            RIGHT: (row, col+2)}

    pdir_1st = {}
    pdir_2nd = {}
    typetwo_keys = []
    for key in pdir.keys():
        checkres = is_valid_position(data, pdir[key])
        if checkres == 1:
            pdir_1st[key] = pdir[key]
        elif checkres == 2:
            pdir_2nd[key] = pdir[key]

    return pdir_1st, pdir_2nd


def is_valid_position(data, (r, c)):
    nrows = len(data)
    ncols = len(data[0])
    if r < 1:
        return 0
    if r > nrows-2:
        return 0
    if c < 1:
        return 0
    if c > ncols-2:
        return 0

    if data[r][c] == '@':
        return 1
    elif data[r][c] == ' ':
        return 2

    return 0

def get_middle_xp(acoords, bcoords):
    if acoords[0] < bcoords[0]:
        return (acoords[0]+1, acoords[1])
    if acoords[0] > bcoords[0]:
        return (acoords[0]-1, acoords[1])
    if acoords[1] < bcoords[1]:
        return (acoords[0], acoords[1]+1)
    if acoords[1] > bcoords[1]:
        return (acoords[0], acoords[1]-1)
    print 'WRONG', acoords, bcoords
    sys.exit(1)

def pmaze(data):
    newdata = []
    for line in data:
        strline = ''
        for ele in line:
            strline += ele
        newdata.append(strline.replace('@','*'))

    pprint(newdata)

def print_maze(DISPLAYSURF, data, level):
    newdata = []
    for line in data:
        strline = ''
        for ele in line:
            strline += ele
        newdata.append(strline.replace('@','*'))

    level.set_data(newdata)

    DISPLAYSURF.fill((0,0,0))
    # analyze the data to assign tiles
    level.analyze_data(DISPLAYSURF)

    level.draw(DISPLAYSURF)


def randmaze(nrows, ncols):

    global xp_isolate, xp_visited, DISPLAYSURF, BASICFONT

    # dimensions must be odd numbers
    assert nrows % 2 == 1
    assert ncols % 2 == 1

    rc = nrows/2
    cc = ncols/2

    data = []

    # all walls initially, these walls 
    for jj in range(nrows):
        data.append(list('@'*ncols))

    # get all the cross points
    row_cross = range(1, nrows, 2)
    col_cross = range(1, ncols, 2)
    # add all of them of isolate first
    for rx in row_cross:
        for cx in col_cross: 
            coords = (rx, cx)
            add_to_isolate((rx, cx))

    # Add the ghost chamber
    ghost_chamber = [
            list('###3###'), 
            list('#**=**#'), 
            list('#*012*#'), 
            list('#*****#'),
            list('#######')
            ]
    for row in [rc-2, rc-1, rc, rc+1, rc+2]:
        for col in [cc-3, cc-2, cc-1, cc, cc+1, cc+2, cc+3]:
            symbol = ghost_chamber[row-(rc-2)][col-(cc-3)]
            data[row][col] = symbol

    for row in [rc-1, rc, rc+1]:
        for col in [cc-2, cc-1, cc, cc+1, cc+2]:
            if row % 2 ==1 and col % 2 == 1:
                #if (row, col) not in [(rc-2,cc-1),(rc-2,cc+1),(rc,cc-3),(rc,cc+3),
                #        (rc+2,cc-3),(rc+2,cc+3)]:
                add_to_visited((row, col))

    

    pygame.init()
    level = eatman.Level()

    WINDOW_WIDTH = ncols*eatman.TILE_WIDTH
    WINDOW_HEIGHT = (nrows+5)*eatman.TILE_HEIGHT
    DISPLAYSURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    eatman.BASICFONT = pygame.font.Font('freesansbold.ttf', 18)

    eatman.resource.load_tiles()
    eatman.resource.load_sounds()
    eatman.resource.load_sprites()

    # recolor the tiles according to the level requirement
    eatman.resource.recolor_tiles(level)

    # start the walking from a random cross point
    c_coords = random.choice(xp_isolate.keys())
    data[c_coords[0]][c_coords[1]] = ' '
    add_to_visited(c_coords)

    while len(xp_isolate) > 0:

        while True:
            movetos_1st, movetos_2nd = get_random_direction(c_coords, data)
            if movetos_1st == {}:
                keys = movetos_2nd.keys()
                random.shuffle(keys)
                n_coords = movetos_2nd[keys[0]]
                m_coords = get_middle_xp(c_coords, n_coords)
                data[m_coords[0]][m_coords[1]] = ' '

                assert c_coords in xp_visited.keys()
                assert n_coords in xp_visited.keys()

                while len(xp_isolate) > 0:
                    new_coords, from_coords = xp_stack.pop()
                    if new_coords in xp_visited.keys():
                        continue
                    else:
                        break

                assert from_coords in xp_visited.keys()

                m_coords = get_middle_xp(new_coords, from_coords)

                data[m_coords[0]][m_coords[1]] = ' '
                data[new_coords[0]][new_coords[1]] = ' '

                add_to_visited(new_coords)

                c_coords = new_coords

                #print_maze(DISPLAYSURF, data, level)
                #pygame.display.update()

                if len(xp_isolate) == 0:
                    print 'Done'
                    return DISPLAYSURF, data, level

            else:
                movetos = movetos_1st
                break

        keys = movetos.keys()
        random.shuffle(keys)
        for key in keys[1:]: 
            push_to_stack(movetos[key], c_coords)

        n_coords = movetos[keys[0]]
        m_coords = get_middle_xp(n_coords, c_coords)

        data[m_coords[0]][m_coords[1]] = ' '
        data[n_coords[0]][n_coords[1]] = ' '

        add_to_visited(n_coords)

        c_coords = n_coords

        #print_maze(DISPLAYSURF, data, level)

        #pygame.display.update()

    return DISPLAYSURF, data, level


if __name__ == '__main__':

    for ii in range(1):
        DISPLAYSURF, data, level = randmaze(25, 37)
        print_maze(DISPLAYSURF, data, level)
        pygame.display.update()

