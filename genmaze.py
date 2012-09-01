#!/usr/bin/env python

import random
from pprint import pprint

TILE_BEAN = '.'
TILE_WALL = '@'
TILE_FIXED_BARRIER = '*'
TILE_VACANCY = ' '
TILE_FIXED_PATH = '#'
TILE_EATMAN = 'e'


class Tile(object):

    def __init__(self, (row, col), symbol):
        self.pos = (row, col)
        self.symbol = symbol
        self.links = []


def format_maze(tiles, nrows, ncols):
    # the eatman position
    re = nrows/2
    ce = ncols/2
    if re % 2 == 0:
        re += 5
    else:
        re += 6
    if re > nrows-2:
        re = nrows-2
    if ce %2 == 0:
        ce -= 1

    # the big beans
    pos_bigbeans = [(3,1), (3,ncols-2), (nrows-4,1), (nrows-4,ncols-2)]

    # format the maze
    data = []
    for row in range(nrows):
        oneline = ''
        for col in range(ncols):
            pos = (row, col)
            if row == re and col == ce:
                oneline += TILE_EATMAN
            elif (row,col) in pos_bigbeans:
                oneline += 'O'
            else:
                oneline += tiles[pos].symbol

        oneline = oneline.replace(TILE_WALL, TILE_FIXED_BARRIER)
        oneline = oneline.replace(TILE_BEAN, TILE_VACANCY)
        data.append(oneline)
        print oneline
    return data


def pmaze(tiles, nrows, ncols):
    data = []
    for row in range(nrows):
        oneline = ''
        for col in range(ncols):
            pos = (row, col)
            oneline += tiles[pos].symbol
        data.append(oneline)

    pprint(data)

def repair_corner_fixed_path(tiles, fpath, tile_1, tile_2, tile_3):

    nemptys = 0
    # first check if we have a corner of four vacancy, if so a repair may need
    candidates = []
    # we do not want make any fixed path as candidate
    fixed_symbols = ['3'] #[TILE_FIXED_PATH, '3']
    if tile_1.symbol in [TILE_VACANCY, TILE_BEAN, TILE_FIXED_PATH, '3']: # vacancy
        nemptys += 1
        if tile_1.symbol not in  fixed_symbols:
            candidates.append(tile_1)
    if tile_2.symbol in [TILE_VACANCY, TILE_BEAN, TILE_FIXED_PATH, '3']:
        nemptys += 1
        if tile_2.symbol not in fixed_symbols:
            candidates.append(tile_2)
    if tile_3.symbol in [TILE_VACANCY, TILE_BEAN, TILE_FIXED_PATH, '3']:
        nemptys += 1
        if tile_3.symbol not in fixed_symbols:
            candidates.append(tile_3)

    if nemptys == 3: # 3 empty plus the fixed path itself, we now have 4 vacancy
        random.shuffle(candidates)
        for cand in candidates:
            possible = True
            # now we check if we can make the candidate a wall and do not
            # make any adjacent vacancy become a dead end
            row_cand, col_cand = cand.pos
            emptys = [TILE_VACANCY, TILE_BEAN, TILE_FIXED_PATH]
            if tiles[(row_cand-1, col_cand)].symbol in emptys:
                if get_nwalls_surrounded(tiles, (row_cand-1, col_cand)) >= 2:
                    continue
            if tiles[(row_cand+1, col_cand)].symbol in emptys:
                if get_nwalls_surrounded(tiles, (row_cand+1, col_cand)) >= 2:
                    continue
            if tiles[(row_cand, col_cand-1)].symbol in emptys:
                if get_nwalls_surrounded(tiles, (row_cand, col_cand-1)) >= 2:
                    continue
            if tiles[(row_cand, col_cand+1)].symbol in emptys:
                if get_nwalls_surrounded(tiles, (row_cand, col_cand+1)) >= 2:
                    continue

            # do not make blocky walls
            # upper left
            if tiles[(row_cand-1,col_cand-1)].symbol == TILE_WALL \
                    and tiles[(row_cand-1,col_cand)].symbol == TILE_WALL \
                    and tiles[(row_cand,col_cand-1)].symbol == TILE_WALL:
                continue
            # upper right
            if tiles[(row_cand-1,col_cand+1)].symbol == TILE_WALL \
                    and tiles[(row_cand-1,col_cand)].symbol == TILE_WALL \
                    and tiles[(row_cand,col_cand+1)].symbol == TILE_WALL:
                continue
            # lower left
            if tiles[(row_cand+1,col_cand-1)].symbol == TILE_WALL \
                    and tiles[(row_cand+1,col_cand)].symbol == TILE_WALL \
                    and tiles[(row_cand,col_cand-1)].symbol == TILE_WALL:
                continue
            # lower right
            if tiles[(row_cand+1,col_cand+1)].symbol == TILE_WALL \
                    and tiles[(row_cand+1,col_cand)].symbol == TILE_WALL \
                    and tiles[(row_cand,col_cand+1)].symbol == TILE_WALL:
                continue

            cand.symbol = TILE_WALL

            print fpath.pos, cand.pos
            pmaze(tiles, 21, 21)


def get_nwalls_surrounded(tiles, pos):
    row, col = pos
    nwalls = 0
    if tiles[(row-1, col)].symbol in [TILE_WALL, TILE_FIXED_BARRIER]:
        nwalls += 1
    if tiles[(row+1, col)].symbol in [TILE_WALL, TILE_FIXED_BARRIER]:
        nwalls += 1
    if tiles[(row, col-1)].symbol in [TILE_WALL, TILE_FIXED_BARRIER]:
        nwalls += 1
    if tiles[(row, col+1)].symbol in [TILE_WALL, TILE_FIXED_BARRIER]:
        nwalls += 1
    return nwalls


def get_new_wall_link(tiles, wall):
    row, col = wall.pos

    candidates = []
    # get possible links from all 4 directions
    if tiles[(row-2, col)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        candidates.append((row-2, col))
    if tiles[(row+2, col)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        candidates.append((row+2, col))
    if tiles[(row, col-2)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        candidates.append((row, col-2))
    if tiles[(row, col+2)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        candidates.append((row, col+2))

    # check if any links are already build or if we trying to link 
    # one wall and two fixed path. We need to disqualify them
    if tiles[(row-1,col)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        if (row-2,col) in candidates:
            candidates.remove((row-2,col))
    if tiles[(row+1,col)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        if (row+2,col) in candidates:
            candidates.remove((row+2,col))
    if tiles[(row,col-1)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        if (row,col-2) in candidates:
            candidates.remove((row,col-2))
    if tiles[(row,col+1)].symbol in [TILE_WALL, TILE_FIXED_PATH]:
        if (row,col+2) in candidates:
            candidates.remove((row,col+2))

    # check if any link would make a vacancy become surrounded by 3 or more walls
    # and disqualify them
    if get_nwalls_surrounded(tiles, (row-1, col-1)) >=2: # upper left
        if (row-2,col) in candidates:
            candidates.remove((row-2,col))
        if (row,col-2) in candidates:
            candidates.remove((row,col-2))
    if get_nwalls_surrounded(tiles, (row-1, col+1)) >=2: # upper right
        if (row-2,col) in candidates:
            candidates.remove((row-2,col))
        if (row,col+2) in candidates:
            candidates.remove((row,col+2))
    if get_nwalls_surrounded(tiles, (row+1, col-1)) >=2: # lower left
        if (row+2,col) in candidates:
            candidates.remove((row+2,col))
        if (row,col-2) in candidates:
            candidates.remove((row,col-2))
    if get_nwalls_surrounded(tiles, (row+1, col+1)) >=2: # lower right
        if (row+2,col) in candidates:
            candidates.remove((row+2,col))
        if (row,col+2) in candidates:
            candidates.remove((row,col+2))

    # choose the link randomly
    if len(candidates) > 0:
        pos_link = random.choice(candidates)
        return tiles[pos_link]
    else:
        return None



def genmaze(nrows, ncols, path_fill_ratio=0.33):

    assert nrows >= 11
    assert ncols >= 11

    # dimensions must be odd numbers
    assert nrows % 2 == 1
    assert ncols % 2 == 1

    rc = nrows/2
    cc = ncols/2

    max_nlinks = ((nrows/2)+1-2)*(nrows/2) + ((ncols/2)+1-2)*(ncols/2)
    
    tiles = {}

    # First populate the maze as all beans
    # The positions of beans are where the walls can be connected
    # and the beans change to walls
    for row in range(nrows):
        for col in range(ncols):
            pos = (row, col)
            tiles[pos] = Tile(pos, TILE_BEAN)

    # The surrounding walls
    for col in range(ncols):
        tiles[(0,col)].symbol = TILE_WALL
        tiles[(nrows-1,col)].symbol = TILE_WALL
    for row in range(nrows):
        tiles[(row,0)].symbol = TILE_WALL
        tiles[(row,ncols-1)].symbol = TILE_WALL

    # The vacant cross points
    for row in range(1,nrows-1,2):
        for col in range(1,ncols-1,2):
            tiles[(row,col)].symbol = TILE_VACANCY

    # The wall'd cross points
    for row in range(0,nrows,2):
        for col in range(0,ncols,2):
            tiles[(row,col)].symbol = TILE_WALL

    # The ghost chamber
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
            tiles[(row,col)].symbol = symbol

    # count the symbol categories
    beans = []
    vacants = []
    walls = []
    fpaths = []
    for row in range(nrows):
        for col in range(ncols):
            pos = (row, col)
            symbol = tiles[pos].symbol
            if symbol == TILE_BEAN:
                beans.append(tiles[pos])
            elif symbol == TILE_VACANCY:
                vacants.append(tiles[pos])
            elif symbol == TILE_WALL \
                    and (row != 0 and row != nrows-1 and col != 0 and col != ncols-1):
                # only consider the inner walls
                walls.append(tiles[pos])
            elif symbol == TILE_FIXED_PATH:
                fpaths.append(tiles[pos])


    # The walls are all isolated at the beginning
    walls_n_links = {}
    walls_n_links[0] = []
    walls_n_links[1] = []
    walls_n_links[2] = []
    walls_n_links[3] = []
    walls_n_links[4] = []
    for wall in walls:
        walls_n_links[0].append(wall)

    nlinks = 0
    done = False
    for nn in range(0,4):
        walls_pool = walls_n_links[nn]
        while len(walls_pool) > 0:
            wall = random.choice(walls_pool)
            row, col = wall.pos

            # get the link candidate
            newlink_wall = get_new_wall_link(tiles, wall)
            # if this wall can not be build further, we remove it
            if newlink_wall is None:
                walls_pool.remove(wall)
                continue

            row_link, col_link = newlink_wall.pos

            # Build the link by change the beans in between into wall
            if row < row_link:
                tiles[(row+1,col)].symbol = TILE_WALL
            elif row > row_link:
                tiles[(row-1,col)].symbol = TILE_WALL
            elif col < col_link:
                tiles[(row,col+1)].symbol = TILE_WALL
            elif col > col_link:
                tiles[(row,col-1)].symbol = TILE_WALL

            # update the wall link numbers
            walls_n_links[len(wall.links)].remove(wall)
            wall.links.append((row_link, col_link))
            walls_n_links[len(wall.links)].append(wall)
            newlink_wall = tiles[(row_link, col_link)]
            if newlink_wall in walls:
                walls_n_links[len(newlink_wall.links)].remove(newlink_wall)
                newlink_wall.links.append((row, col))
                walls_n_links[len(newlink_wall.links)].append(newlink_wall)

            # total number of links
            nlinks += 1

            # check if have build enough number of links
            if nlinks*1.0/max_nlinks > path_fill_ratio and len(walls_n_links[0])==0:
                done = True
                break

        if done:
            break

    # print the maze
    pmaze(tiles, nrows, ncols)

    # make sure the surroudings of the ghost chamber have no double lanes
    random.shuffle(fpaths)
    for fpath in fpaths:
        row, col = fpath.pos
        # the nine tiles surround it
        tile_l = tiles[row,col-1]
        tile_r = tiles[row,col+1]
        tile_u = tiles[row-1,col]
        tile_d = tiles[row+1,col]
        tile_ul = tiles[row-1,col-1]
        tile_ur = tiles[row-1,col+1]
        tile_ll = tiles[row+1,col-1]
        tile_lr = tiles[row+1,col+1]

        # upper left
        repair_corner_fixed_path(tiles, fpath, tile_u, tile_l, tile_ul)

        # upper right
        repair_corner_fixed_path(tiles, fpath, tile_u, tile_r, tile_ur)

        # lower left
        repair_corner_fixed_path(tiles, fpath, tile_l, tile_l, tile_ll)

        # lower right
        repair_corner_fixed_path(tiles, fpath, tile_l, tile_r, tile_lr)



    # make sure the entire maze are connected


    # print the maze
    pmaze(tiles, nrows, ncols)

    return format_maze(tiles, nrows, ncols)



if __name__ == '__main__':

    genmaze(21, 21)


