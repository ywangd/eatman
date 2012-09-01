#!/usr/bin/env python

import sys, random
from pprint import pprint

TILE_BEAN               = '.'
TILE_WALL               = '@'
TILE_FIXED_BARRIER      = '*'
TILE_VACANCY            = ' '
TILE_FIXED_PATH         = '#'
TILE_EATMAN             = 'e'


class Tile(object):

    def __init__(self, (row, col), symbol):
        self.pos = (row, col)
        self.symbol = symbol
        self.links = []


def format_maze(tiles, nrows, ncols):

    # the big beans
    pos_bigbeans = [(3,1), (3,ncols-2), (nrows-4,1), (nrows-4,ncols-2)]

    # format the maze
    data = []
    for row in range(nrows):
        oneline = ''
        for col in range(ncols):
            pos = (row, col)
            if (row,col) in pos_bigbeans:
                oneline += 'O'
            else:
                oneline += tiles[pos].symbol

        oneline = oneline.replace(TILE_WALL, TILE_FIXED_BARRIER)
        oneline = oneline.replace(TILE_BEAN, TILE_VACANCY)
        data.append(oneline)
        #print oneline
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



def get_possible_path(tiles, cell, cells_unvisited):
    '''
    Get all possible path around the given cell.
    '''
    possible_path = []
    passable_cells = [TILE_BEAN, TILE_VACANCY, TILE_FIXED_PATH, TILE_EATMAN]
    row, col = cell.pos
    # up
    up_cell = tiles[(row-1,col)]
    if up_cell.symbol in passable_cells and up_cell in cells_unvisited:
        possible_path.append(up_cell)
    # down
    down_cell = tiles[(row+1,col)]
    if down_cell.symbol in passable_cells and down_cell in cells_unvisited:
        possible_path.append(down_cell)
    # left
    left_cell = tiles[(row,col-1)]
    if left_cell.symbol in passable_cells and left_cell in cells_unvisited:
        possible_path.append(left_cell)
    # right
    right_cell = tiles[(row,col+1)]
    if right_cell.symbol in passable_cells and right_cell in cells_unvisited:
        possible_path.append(right_cell)

    return possible_path

def is_possible_breakage(tiles, nrows, ncols, cell, cells_visited):
    row, col = cell.pos
    if row >= 3 and tiles[(row-2,col)] in cells_visited and tiles[(row-1,col)].symbol==TILE_WALL:
        return True
    if row <= nrows-4 and tiles[(row+2,col)] in cells_visited and tiles[(row+1,col)].symbol==TILE_WALL:
        return True
    if col >= 3 and tiles[(row,col-2)] in cells_visited and tiles[(row,col-1)].symbol==TILE_WALL:
        return True
    if col <= ncols-4 and tiles[(row,col+2)] in cells_visited and tiles[(row,col+1)].symbol==TILE_WALL:
        return True

def break_the_wall(tiles, nrows, ncols, cell, cells_visited):
    row, col = cell.pos
    if row >= 3 and tiles[(row-2,col)] in cells_visited and tiles[(row-1,col)].symbol==TILE_WALL:
        tiles[(row-1,col)].symbol = TILE_VACANCY
        return True
    if row <= nrows-4 and tiles[(row+2,col)] in cells_visited and tiles[(row+1,col)].symbol==TILE_WALL:
        tiles[(row+1,col)].symbol = TILE_VACANCY
        return True
    if col >= 3 and tiles[(row,col-2)] in cells_visited and tiles[(row,col-1)].symbol==TILE_WALL:
        tiles[(row,col-1)].symbol = TILE_VACANCY
        return True
    if col <= ncols-4 and tiles[(row,col+2)] in cells_visited and tiles[(row,col+1)].symbol==TILE_WALL:
        tiles[(row,col+1)].symbol = TILE_VACANCY
        return True



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
            break


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
    '''
    A link is a group of three walls in a horizontal or vertical fashion.
    e.g. @@@ is a horizontal link. The character in the middle is called
    the passage of the link and the both ends are called anchor of the link.
    '''

    row, col = wall.pos # this is our starting anchor and we need to find the ending one

    candidates = []
    # Get possible link anchor from all 4 directions. 
    # The possible links must be between walls.
    possible_anchor = [TILE_WALL]
    if tiles[(row-2, col)].symbol in possible_anchor:
        candidates.append((row-2, col))
    if tiles[(row+2, col)].symbol in possible_anchor:
        candidates.append((row+2, col))
    if tiles[(row, col-2)].symbol in possible_anchor:
        candidates.append((row, col-2))
    if tiles[(row, col+2)].symbol in possible_anchor:
        candidates.append((row, col+2))

    # The links cannot be built through an existing wall or
    # a fixed path or the eatman
    invalid_passage = [TILE_WALL, TILE_FIXED_PATH, TILE_EATMAN]
    if tiles[(row-1,col)].symbol in invalid_passage:
        if (row-2,col) in candidates:
            candidates.remove((row-2,col))
    if tiles[(row+1,col)].symbol in invalid_passage:
        if (row+2,col) in candidates:
            candidates.remove((row+2,col))
    if tiles[(row,col-1)].symbol in invalid_passage:
        if (row,col-2) in candidates:
            candidates.remove((row,col-2))
    if tiles[(row,col+1)].symbol in invalid_passage:
        if (row,col+2) in candidates:
            candidates.remove((row,col+2))

    # Check if any link would make a vacancy become surrounded by 3 
    # or more walls. We need to disqualify them. 
    # The vacancy are those adjacent to the link's passage
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

    assert nrows >= 13
    assert ncols >= 13

    # dimensions must be odd numbers and the half of it must be an even number
    assert nrows % 2 == 1 and (nrows/2) % 2 == 0
    assert ncols % 2 == 1 and (ncols/2) % 2 == 0

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
    for row in [rc-3, rc-2, rc-1, rc, rc+1]:
        for col in [cc-3, cc-2, cc-1, cc, cc+1, cc+2, cc+3]:
            symbol = ghost_chamber[row-(rc-3)][col-(cc-3)]
            tiles[(row,col)].symbol = symbol

    # The eatman's location
    tiles[(rc+5,cc)].symbol = TILE_EATMAN

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

    #pmaze(tiles, nrows, ncols)
    #format_maze(tiles, nrows, ncols)

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
    #pmaze(tiles, nrows, ncols)
    #format_maze(tiles, nrows, ncols)
    
    #
    # The following section is not needed since there will be no double lanes
    # after we move the ghost chamber to the correct position.
    #
    # make sure the surroudings of the ghost chamber have no double lanes
    #random.shuffle(fpaths)
    #for fpath in fpaths:
    #    row, col = fpath.pos
    #    # the nine tiles surround it
    #    tile_l = tiles[row,col-1]
    #    tile_r = tiles[row,col+1]
    #    tile_u = tiles[row-1,col]
    #    tile_d = tiles[row+1,col]
    #    tile_ul = tiles[row-1,col-1]
    #    tile_ur = tiles[row-1,col+1]
    #    tile_ll = tiles[row+1,col-1]
    #    tile_lr = tiles[row+1,col+1]
    #    # upper left
    #    repair_corner_fixed_path(tiles, fpath, tile_u, tile_l, tile_ul)
    #    # upper right
    #    repair_corner_fixed_path(tiles, fpath, tile_u, tile_r, tile_ur)
    #    # lower left
    #    repair_corner_fixed_path(tiles, fpath, tile_l, tile_l, tile_ll)
    #    # lower right
    #    repair_corner_fixed_path(tiles, fpath, tile_l, tile_r, tile_lr)

    #format_maze(tiles, nrows, ncols)
    # make sure the entire maze are connected
    # TODO:
    #  check if the breakage make holes (a block of vacany)
    #  possiblity of more than 2 isolated parts of the maze?
    cells_unvisited = []
    cells_visited = []
    cells_stack = []
    for row in range(nrows):
        for col in range(ncols):
            pos = (row, col)
            passable_cells = [TILE_BEAN, TILE_VACANCY, TILE_FIXED_PATH, TILE_EATMAN]
            if tiles[pos].symbol in passable_cells:
                cells_unvisited.append(tiles[pos])
    # start walking the cells
    random.shuffle(cells_unvisited)
    cells_stack.append(cells_unvisited[0])
    while len(cells_stack) > 0:
        c_cell = cells_stack.pop()
        possible_path = get_possible_path(tiles, c_cell, cells_unvisited)
        for pp in possible_path:
            if pp not in cells_stack:
                cells_stack.append(pp)
        cells_unvisited.remove(c_cell)
        cells_visited.append(c_cell)

    # if the maze are not connected
    cells_possible_breakage = []
    if len(cells_unvisited) > 0:
        # the breakable ones
        for cell in cells_unvisited:
            if is_possible_breakage(tiles, nrows, ncols, cell, cells_visited):
                cells_possible_breakage.append(cell)
        # The most separated ones 
        maxdist = 0
        for cell_1 in cells_possible_breakage:
            for cell_2 in cells_possible_breakage:
                if cell_1 is cell_2:
                    continue
                dist = (cell_1.pos[0]-cell_2.pos[0])**2 + (cell_1.pos[1]-cell_2.pos[1])**2
                if maxdist < dist:
                    maxdist = dist
                    pair = [cell_1, cell_2]

        break_the_wall(tiles, nrows, ncols, pair[0], cells_visited)
        break_the_wall(tiles, nrows, ncols, pair[1], cells_visited)


    # print the maze
    #pmaze(tiles, nrows, ncols)

    return format_maze(tiles, nrows, ncols)



if __name__ == '__main__':

    genmaze(21, 21)

