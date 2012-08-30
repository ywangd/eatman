#!/usr/bin/env python
'''
Generate a random maze for EatMan.
'''
import sys, random
from pprint import pprint

xp_isolate = {}
xp_connect = {}

# how many cross points for each type, i.e. only one other cross point
# is linked to them, 2 cross points lined to them etc.
xp_nlinks = {0:0, 1:0, 2:0, 3:0, 4:0}


def add_to_isolate((r, c)):
    global xp_isolate, xp_connect, xp_nlinks
    key = (r, c)
    if xp_connect.has_key(key):
        del xp_connect[key]
    xp_isolate[(r,c)] = []
    xp_nlinks[0] += 1

def add_to_connect((r, c), neighbours):
    global xp_isolate, xp_connect, xp_nlinks
    key = (r, c)
    if xp_isolate.has_key(key):
        del xp_isolate[key]

    if xp_connect.has_key(key):
        xp_nlinks[len(xp_connect[key])] -= 1
        for ngh in neighbours:
            if ngh not in xp_connect[key]:
                xp_connect[key].append(ngh)
        xp_nlinks[len(xp_connect[key])] += 1
    else:
        xp_connect[key] = neighbours
        xp_nlinks[len(neighbours)] += 1



def get_random_direction(scoords, ecoords, data):
    row, col = scoords
    nrows = len(data)
    ncols = len(data[0])

    UP = 'u'
    LEFT = 'l'
    DOWN = 'd'
    RIGHT = 'r'

    pdir = {
            UP: (row-2, col), 
            LEFT: (row, col-2), 
            DOWN: (row+2, col), 
            RIGHT: (row, col+2)}

    if row-2 < 1:
        del pdir[UP]
    if row+2 > nrows-2:
        del pdir[DOWN]
    if col-2 < 1:
        del pdir[LEFT]
    if col+2 > ncols-2:
        del pdir[RIGHT]

    mindist = 1e20
    keys = pdir.keys()
    random.shuffle(keys)
    for key in keys:
        if is_valid_position(data, pdir[key]):
            dist = calc_distsq(scoords, pdir[key])
            if mindist > dist:
                mindist = dist
                moveto = key

    return moveto


def calc_distsq(spos, epos):
    return (spos[0]-epos[0])**2 + (spos[1]-epos[1])**2

def is_valid_position(data, (r, c)):
    if data[r][c] in ['@', ' ']:
        return True
    else:
        return False



def print_maze(data):
    for line in data:
        strline = ''
        for ele in line:
            strline += ele
        print strline.replace('@','*')

def randmaze(nrows, ncols):

    global xp_isolate, xp_connect

    # dimensions must be odd numbers
    assert nrows % 2 == 1
    assert ncols % 2 == 1

    rc = nrows/2
    cc = ncols/2

    data = []

    # all walls initially, these walls 
    for jj in range(nrows):
        data.append(list('@'*ncols))

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

    # 1st line
    add_to_connect((rc-2,cc-3), [(rc-2,cc-2),(rc-1,cc-3)])
    add_to_connect((rc-2,cc-2), [(rc-2,cc-3),(rc-2,cc-1)])
    add_to_connect((rc-2,cc-1), [(rc-2,cc-2)])
    add_to_connect((rc-2,cc+1), [(rc-2,cc+2)])
    add_to_connect((rc-2,cc+2), [(rc-2,cc+1),(rc-2,cc+3)])
    add_to_connect((rc-2,cc+3), [(rc-2,cc+2),(rc-1,cc+3)])

    # 2nd line
    add_to_connect((rc-1,cc-3), [(rc-2,cc-3),(rc,cc-3)])
    add_to_connect((rc-1,cc+3), [(rc-2,cc+3),(rc,cc+3)])

    # 3rd line
    add_to_connect((rc,cc-3), [(rc-1,cc-3),(rc+1,cc-3)])
    add_to_connect((rc,cc+3), [(rc-1,cc+3),(rc+1,cc+3)])

    # 4th line
    add_to_connect((rc+1,cc-3), [(rc,cc-3),(rc+2,cc-3)])
    add_to_connect((rc+1,cc+3), [(rc,cc+3),(rc+2,cc+3)])

    # 5th line
    add_to_connect((rc+2,cc-3), [(rc+2,cc-2),(rc+1,cc-3)])
    add_to_connect((rc+2,cc-2), [(rc+2,cc-3),(rc+2,cc-1)])
    add_to_connect((rc+2,cc-1), [(rc+2,cc-2),(rc+2,cc)])
    add_to_connect((rc+2,cc), [(rc+2,cc-1),(rc+2,cc+1)])
    add_to_connect((rc+2,cc+1), [(rc+2,cc+2),(rc+2,cc)])
    add_to_connect((rc+2,cc+2), [(rc+2,cc+1),(rc+2,cc+3)])
    add_to_connect((rc+2,cc+3), [(rc+2,cc+2),(rc+1,cc+3)])

    
    # get all the cross points
    row_cross = range(1, nrows, 2)
    col_cross = range(1, ncols, 2)
    # list of cross points in chamber area
    xp_in_chamber = [(rc-1,cc-3), (rc-1,cc-1), (rc-1,cc+1), (rc-1,cc+3),
            (rc+1,cc-3), (rc+1,cc-1), (rc+1,cc), (rc+1,cc+1), (rc+1,cc+3)]
    for rx in row_cross:
        for cx in col_cross: 
            coords = (rx, cx)
            if coords not in xp_in_chamber:
                add_to_isolate((rx, cx))

    # start the walking from a random cross point
    scoords = random.choice(xp_isolate.keys())
    ecoords = random.choice(xp_isolate.keys())

    while len(xp_isolate) > 0:

        if scoords == ecoords:
            scoords = random.choice(xp_isolate.keys())
            ecoords = random.choice(xp_isolate.keys())
            print 'wrong'
            sys.exit(1)

        else:
            moveto = get_random_direction(scoords, ecoords, data)
            if moveto == 'u':
                newcoords = (scoords[0]-2, scoords[1])
                data[scoords[0]-1][scoords[1]] = ' '
                
            elif moveto == 'd':
                newcoords = (scoords[0]+2, scoords[1])
                data[scoords[0]+1][scoords[1]] = ' '

            elif moveto == 'l':
                newcoords = (scoords[0], scoords[1]-2)
                data[scoords[0]][scoords[1]-1] = ' '

            elif moveto == 'r':
                newcoords = (scoords[0], scoords[1]+2)
                data[scoords[0]][scoords[1]+1] = ' '

            add_to_connect(scoords, [newcoords])
            add_to_connect(newcoords, [scoords])

            data[scoords[0]][scoords[1]] = ' '
            data[newcoords[0]][newcoords[1]] = ' '

            if newcoords == ecoords:
                if len(xp_isolate) > 0:
                    scoords = random.choice(xp_isolate.keys())
                    ecoords = random.choice(xp_isolate.keys())
            else:
                scoords = newcoords



    print_maze(data)



if __name__ == '__main__':

    randmaze(21, 21)
