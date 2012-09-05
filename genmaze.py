#!/usr/bin/env python

import sys, random
from string import maketrans
from pprint import pprint

TILE_BEAN               = '.'
TILE_WALL               = '@'
TILE_FIXED_BARRIER      = '*'
TILE_VACANCY            = ' '
TILE_FIXED_PATH         = '#'
TILE_EATMAN             = 'e'
TILE_TELEPORT           = '$'


class Tile(object):

    def __init__(self, (row, col), symbol):
        self.pos = (row, col)
        self.symbol = symbol
        self.links = []


def format_maze(tiles, nrows, ncols, printit=False):

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
        if printit: 
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


def get_possible_path(tiles, cell, cells_unvisited, 
        passable_cells=[TILE_BEAN, TILE_VACANCY, TILE_FIXED_PATH, TILE_EATMAN]):
    '''
    Get all possible path around the given cell.
    '''
    possible_path = []
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


def is_forming_blocky(tiles, cell, blocky_type):
    # make sure we are not making blocky type 
    row, col = cell.pos 
    tile_l = tiles[row, col-1]
    tile_r = tiles[row, col+1]
    tile_u = tiles[row-1, col]
    tile_d = tiles[row+1, col]
    tile_ul = tiles[row-1, col-1]
    tile_ur = tiles[row-1, col+1]
    tile_ll = tiles[row+1, col-1]
    tile_lr = tiles[row+1, col+1]
    # upper left
    if not(tile_u in blocky_type and tile_l in blocky_type and tile_ul in blocky_type) \
            and not(tile_u in blocky_type and tile_r in blocky_type and tile_ur in blocky_type) \
            and not(tile_d in blocky_type and tile_l in blocky_type and tile_ll in blocky_type) \
            and not(tile_d in blocky_type and tile_r in blocky_type and tile_lr in blocky_type):
        return False # no blocky is forming

    return True


def find_possible_breakage(tiles, nrows, ncols, cell, cells_visited):
    '''
    Check whether the given cell is a possible position to make a breakage around it.
    '''
    row, col = cell.pos
    passable_cells = [TILE_BEAN, TILE_VACANCY, TILE_FIXED_PATH, TILE_EATMAN]

    # UP 
    # Make sure the cell to break is a wall and the breakage is going to a visited space
    if row >= 3 and tiles[(row-2,col)] in cells_visited and tiles[(row-1,col)].symbol==TILE_WALL:
        if is_forming_blocky(tiles, tiles[(row-1, col)], passable_cells) == False:
            return (row-1, col)

    # DOWN
    if row <= nrows-4 and tiles[(row+2,col)] in cells_visited and tiles[(row+1,col)].symbol==TILE_WALL:
        if is_forming_blocky(tiles, tiles[(row+1, col)], passable_cells) == False:
            return (row+1, col)


    # LEFT
    if col >= 3 and tiles[(row,col-2)] in cells_visited and tiles[(row,col-1)].symbol==TILE_WALL:
        if is_forming_blocky(tiles, tiles[(row, col-1)], passable_cells) == False:
            return (row, col-1)


    #RIGHT
    if col <= ncols-4 and tiles[(row,col+2)] in cells_visited and tiles[(row,col+1)].symbol==TILE_WALL:
        if is_forming_blocky(tiles, tiles[(row, col+1)], passable_cells) == False:
            return (row, col+1)

    return None


def count_nwalls_surrounded(tiles, pos):
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


def get_new_wall_link(tiles, nrows, ncols, wall):
    '''
    A link is a group of three walls in a horizontal or vertical fashion.
    e.g. @@@ is a horizontal link. The character in the middle is called
    the passage of the link and the both ends are called anchor of the link.
    '''
    # this is our starting anchor and we need to find the ending one
    row, col = wall.pos 

    # possible links from 4 directions
    POS_UP          = (row-2, col)
    POS_DOWN        = (row+2, col)
    POS_LEFT        = (row, col-2)
    POS_RIGHT       = (row, col+2)
    candidates = []
    # Get possible link anchor from all 4 directions. 
    # The possible links must be between walls.
    possible_anchor = [TILE_WALL]
    if tiles[POS_UP].symbol in possible_anchor:
        candidates.append(POS_UP)
    if tiles[POS_DOWN].symbol in possible_anchor:
        candidates.append(POS_DOWN)
    if tiles[POS_LEFT].symbol in possible_anchor:
        candidates.append(POS_LEFT)
    if tiles[POS_RIGHT].symbol in possible_anchor:
        candidates.append(POS_RIGHT)

    # The links cannot be built through an existing wall or
    # a fixed path or the eatman
    invalid_passage = [TILE_WALL, TILE_FIXED_PATH, TILE_EATMAN]
    if POS_UP in candidates and tiles[(row-1,col)].symbol in invalid_passage:
        candidates.remove(POS_UP)
    if POS_DOWN in candidates and tiles[(row+1,col)].symbol in invalid_passage:
        candidates.remove(POS_DOWN)
    if POS_LEFT in candidates and tiles[(row,col-1)].symbol in invalid_passage:
        candidates.remove(POS_LEFT)
    if POS_RIGHT in candidates and tiles[(row,col+1)].symbol in invalid_passage:
        candidates.remove(POS_RIGHT)

    # Check if any link would make a vacancy become surrounded by 3 
    # or more walls. We need to disqualify them. 
    # The vacancy are those adjacent to the link's passage
    nwalls_ul = count_nwalls_surrounded(tiles, (row-1, col-1))  # upper left
    nwalls_ur = count_nwalls_surrounded(tiles, (row-1, col+1))  # upper right
    nwalls_ll = count_nwalls_surrounded(tiles, (row+1, col-1))  # lower left
    nwalls_lr = count_nwalls_surrounded(tiles, (row+1, col+1))  # lower right

    if POS_UP in candidates:
        if nwalls_ul >= 2 or nwalls_ur >= 2:
            candidates.remove(POS_UP)

    if POS_DOWN in candidates:
        if nwalls_ll >= 2 or nwalls_lr >= 2:
            candidates.remove(POS_DOWN)

    if POS_LEFT in candidates:
        if nwalls_ul >= 2 or nwalls_ll >= 2:
            candidates.remove(POS_LEFT)

    if POS_RIGHT in candidates:
        if nwalls_ur >=2 or nwalls_lr >= 2:
            candidates.remove(POS_RIGHT)

    # make sure the walls do not form a U shape
    # The theory is to walk from end to end and see if the walk path
    # is in any of the uld, urd, etc, which are the signs of U shape
    UP = 'u'
    DOWN = 'd'
    LEFT = 'l'
    RIGHT = 'r'
    transtable = maketrans('udlr','durl')

    # walk of the given node
    walk_stack = []
    walk_visited = []
    walk_info = {}
    walk_end = []

    # find the end node
    walk_stack.append(wall) 
    walk_info[wall.pos] = (None, '') # previous node, direction
    is_connected_to_boundary = False
    while len(walk_stack) > 0:

        c_cell = walk_stack.pop()
        c_row, c_col = c_cell.pos
        walk_visited.append(c_cell)
        is_middle_node = False

        # if it is an outter wall tile, add it directly to the end list
        # and do not add any of its neighbours (so the contintue here).
        # This ensure that at most 1 outter wall tile will be counted.
        if c_row <=0 or c_row >= nrows-1 or c_col <= 0 or c_col >= ncols-1:
            is_connected_to_boundary = True
            walk_end.append(c_cell)
            continue

        if c_row-1 > 0:
            up_cell = tiles[(c_row-1,c_col)]
            if up_cell.symbol == TILE_WALL \
                    and up_cell not in walk_visited and up_cell not in walk_stack:
                walk_stack.append(up_cell)
                walk_info[up_cell.pos] = (c_cell, UP)
                is_middle_node = True
        else:
            is_connected_to_boundary = True

        if c_row+1 < nrows-1:
            down_cell = tiles[(c_row+1,c_col)]
            if down_cell.symbol == TILE_WALL \
                    and down_cell not in walk_visited and down_cell not in walk_stack:
                walk_stack.append(down_cell)
                walk_info[down_cell.pos] = (c_cell, DOWN)
                is_middle_node = True
        else:
            is_connected_to_boundary = True

        if c_col-1 > 0:
            left_cell = tiles[(c_row,c_col-1)]
            if left_cell.symbol == TILE_WALL \
                    and left_cell not in walk_visited and left_cell not in walk_stack:
                walk_stack.append(left_cell)
                walk_info[left_cell.pos] = (c_cell, LEFT)
                is_middle_node = True
        else:
            is_connected_to_boundary = True

        if c_col+1 < ncols-1:
            right_cell = tiles[(c_row,c_col+1)]
            if right_cell.symbol == TILE_WALL \
                    and right_cell not in walk_visited and right_cell not in walk_stack:
                walk_stack.append(right_cell)
                walk_info[right_cell.pos] = (c_cell, RIGHT)
                is_middle_node = True
        else:
            is_connected_to_boundary = True

        if not is_middle_node:
            walk_end.append(c_cell)

    # reconstruct the path from the end
    walk_path = {}
    for wend in walk_end:
        p_cell, direction = walk_info[wend.pos]
        walk_path[wend.pos] = direction
        c_cell = p_cell
        while c_cell is not None:
            p_cell, direction = walk_info[c_cell.pos]
            walk_path[wend.pos] += direction
            c_cell = p_cell
        # reverse the path to make it from end to start
        walk_path[wend.pos] = walk_path[wend.pos].translate(transtable)

    # walk of the candidate node
    for ii in range(len(candidates)-1,-1,-1):
        cand = candidates[ii]
        walk_stack_cand = []
        walk_visited_cand = []
        walk_info_cand = {}
        walk_end_cand = []

        # find the ending node
        walk_stack_cand.append(tiles[cand])
        walk_info_cand[cand] = (None, '')
        is_connected_to_boundary_cand = False
        while len(walk_stack_cand) > 0:

            c_cell = walk_stack_cand.pop()
            c_row, c_col = c_cell.pos
            walk_visited_cand.append(c_cell)
            is_middle_node = False

            if c_row <=0 or c_row >= nrows-1 or c_col <= 0 or c_col >= ncols-1:
                is_connected_to_boundary_cand = True
                walk_end_cand.append(c_cell)
                continue

            if c_row-1 > 0:
                up_cell = tiles[(c_row-1,c_col)]
                if up_cell.symbol == TILE_WALL \
                        and up_cell not in walk_visited_cand and up_cell not in walk_stack_cand:
                    walk_stack_cand.append(up_cell)
                    walk_info_cand[up_cell.pos] = (c_cell, UP)
                    is_middle_node = True
            else:
                is_connected_to_boundary_cand = True

            if c_row+1 < nrows-1:
                down_cell = tiles[(c_row+1,c_col)]
                if down_cell.symbol == TILE_WALL \
                        and down_cell not in walk_visited_cand and down_cell not in walk_stack_cand:
                    walk_stack_cand.append(down_cell)
                    walk_info_cand[down_cell.pos] = (c_cell, DOWN)
                    is_middle_node = True
            else:
                is_connected_to_boundary_cand = True

            if c_col-1 > 0:
                left_cell = tiles[(c_row,c_col-1)]
                if left_cell.symbol == TILE_WALL \
                        and left_cell not in walk_visited_cand and left_cell not in walk_stack_cand:
                    walk_stack_cand.append(left_cell)
                    walk_info_cand[left_cell.pos] = (c_cell, LEFT)
                    is_middle_node = True
            else:
                is_connected_to_boundary_cand = True

            if c_col+1 < ncols-1:
                right_cell = tiles[(c_row,c_col+1)]
                if right_cell.symbol == TILE_WALL \
                        and right_cell not in walk_visited_cand and right_cell not in walk_stack_cand:
                    walk_stack_cand.append(right_cell)
                    walk_info_cand[right_cell.pos] = (c_cell, RIGHT)
                    is_middle_node = True
            else:
                is_connected_to_boundary_cand = True

            if not is_middle_node:
                walk_end_cand.append(c_cell)

        # reconstruct the path to the ending nodes
        walk_path_cand = {}
        for wend in walk_end_cand:
            p_cell, direction = walk_info_cand[wend.pos]
            walk_path_cand[wend.pos] = direction
            c_cell = p_cell
            while c_cell is not None:
                p_cell, direction = walk_info_cand[c_cell.pos]
                walk_path_cand[wend.pos] += direction
                c_cell = p_cell
            # reverse the order of the path to make it from start to the end
            walk_path_cand[wend.pos] = walk_path_cand[wend.pos][::-1]

        # check if any of the end nodes make U shape walls
        disqualified = False
        for key1 in walk_path.keys():
            for key2 in walk_path_cand.keys():
                if cand ==  POS_UP:
                    combpath = walk_path[key1] + UP + walk_path_cand[key2]
                elif cand ==  POS_DOWN:
                    combpath = walk_path[key1] + DOWN + walk_path_cand[key2]
                elif cand ==  POS_LEFT:
                    combpath = walk_path[key1] + LEFT + walk_path_cand[key2]
                elif cand ==  POS_RIGHT:
                    combpath = walk_path[key1] + RIGHT + walk_path_cand[key2]

                thepath = combpath[0]
                # eliminate the repeated chars
                for chr in combpath[1:]:
                    if thepath[-1] != chr:
                        thepath += chr

                # Ensure no U shape wall
                if thepath.find('urd') >= 0 \
                        or thepath.find('uld') >= 0 \
                        or thepath.find('lur') >= 0 \
                        or thepath.find('ldr') >= 0 \
                        or thepath.find('dru') >= 0 \
                        or thepath.find('dlu') >= 0 \
                        or thepath.find('rdl') >= 0 \
                        or thepath.find('rul') >= 0:

                    disqualified = True
                    del candidates[ii]
                    break

                # This ensures no L shape wall thats connected to an outter wall, which
                # essentially is another U shape wall
                elif (is_connected_to_boundary or is_connected_to_boundary_cand) \
                        and (thepath.find('ur') >= 0 \
                        or thepath.find('ul') >= 0 \
                        or thepath.find('lu') >= 0 \
                        or thepath.find('ld') >= 0 \
                        or thepath.find('dr') >= 0 \
                        or thepath.find('dl') >= 0 \
                        or thepath.find('rd') >= 0 \
                        or thepath.find('ru') >= 0):

                    disqualified = True
                    del candidates[ii]
                    break

                # Ensure no Z shape wall
                # NOTE: We are not limiting this
                #elif thepath.find('uru') >= 0 \
                #        or thepath.find('ulu') >= 0 \
                #        or thepath.find('lul') >= 0 \
                #        or thepath.find('ldl') >= 0 \
                #        or thepath.find('drd') >= 0 \
                #        or thepath.find('dld') >= 0 \
                #        or thepath.find('rdr') >= 0 \
                #        or thepath.find('rur') >= 0:

                    #disqualified = True
                    #del candidates[ii]
                    #break
                    #pass

                # We can furthur limit the length of the end-to-end path!
                # Its an option.

                #print wall.pos, cand
                #print thepath, walk_path[key1], walk_path_cand[key2]
                #pmaze(tiles, 21, 21)

            if disqualified:
                break


    # Make sure no closed area is forming
    # We cannot merge this simply with the U shape part since they use different wall types
    # walk of the given node
    walk_stack = []
    walk_visited = []

    # we walk the node and see if the candidate nodes can be reach without the new link
    walk_stack.append(wall) 
    wall_tiles = [TILE_WALL, TILE_FIXED_BARRIER]
    while len(walk_stack) > 0:
        c_cell = walk_stack.pop()
        c_row, c_col = c_cell.pos
        walk_visited.append(c_cell)

        if c_row-1 >= 0:
            up_cell = tiles[(c_row-1,c_col)]
            if up_cell.symbol in wall_tiles \
                    and up_cell not in walk_visited and up_cell not in walk_stack:
                walk_stack.append(up_cell)

        if c_row+1 <= nrows-1:
            down_cell = tiles[(c_row+1,c_col)]
            if down_cell.symbol in wall_tiles \
                    and down_cell not in walk_visited and down_cell not in walk_stack:
                walk_stack.append(down_cell)

        if c_col-1 >= 0:
            left_cell = tiles[(c_row,c_col-1)]
            if left_cell.symbol in wall_tiles \
                    and left_cell not in walk_visited and left_cell not in walk_stack:
                walk_stack.append(left_cell)

        if c_col+1 <= ncols-1:
            right_cell = tiles[(c_row,c_col+1)]
            if right_cell.symbol in wall_tiles \
                    and right_cell not in walk_visited and right_cell not in walk_stack:
                walk_stack.append(right_cell)

    # see if we have reached any candidates and delete them
    for ii in range(len(candidates)-1,-1,-1):
        if tiles[candidates[ii]] in walk_visited:
            del candidates[ii]



    # now we can choose the link randomly
    if len(candidates) > 0:
        pos_link = random.choice(candidates)
        return tiles[pos_link]
    else:
        return None



def genmaze(nrows, ncols, path_fill_ratio=0.33):

    assert nrows >= 15
    assert ncols >= 15

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
            '@@@#@#@@@',
            '@###3###@', 
            '@#**=**#@', 
            '##*012*##', 
            '@#*****#@',
            '@#######@',
            '@#@@@@@#@',
            ]
    if rc %2 == 0: # even row center
        rowrange = [rc-4,rc-3, rc-2, rc-1, rc, rc+1,rc+2]
    else:
        rowrange = [rc-3,rc-2, rc-1, rc, rc+1, rc+2,rc+3]
    if cc %2 == 0: # even column center
        colrange = [cc-4, cc-3, cc-2, cc-1, cc, cc+1, cc+2, cc+3, cc+4]
    else:
        colrange = [cc-5, cc-4, cc-3, cc-2, cc-1, cc, cc+1, cc+2, cc+3]
    for row in rowrange:
        for col in colrange:
            symbol = ghost_chamber[row-rowrange[0]][col-colrange[0]]
            tiles[(row,col)].symbol = symbol

    # The tunnel placeholder
    tunnel_left = [
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            ]
    tunnel_right = [
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            '*****',
            ]
    for row in rowrange:
        for col in range(5):
            tiles[(row,col)].symbol = tunnel_left[row-rowrange[0]][col]
            tiles[(row,ncols-1-col)].symbol = tunnel_right[row-rowrange[0]][4-col]

    # The eatman's location
    if rc % 2 == 0:
        re = rc + 5
    else:
        re = rc + 6
    if cc % 2 == 0:
        ce = cc
    else:
        ce = cc - 1
    tiles[(re,ce)].symbol = TILE_EATMAN

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

    #format_maze(tiles, nrows, ncols, printit=True)

    # Form walls randomly
    nlinks = 0
    done = False
    for nn in range(0,4):
        walls_pool = walls_n_links[nn]
        while len(walls_pool) > 0:
            wall = random.choice(walls_pool)
            row, col = wall.pos

            # get the link candidate
            newlink_wall = get_new_wall_link(tiles, nrows, ncols, wall)

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

    #format_maze(tiles, nrows, ncols, printit=True)
    
    ## make sure the entire maze are connected
    ## TODO:
    ##  possiblity of more than 2 isolated parts of the maze?
    #cells_unvisited = []
    #cells_visited = []
    #cells_stack = []
    #for row in range(nrows):
    #    for col in range(ncols):
    #        pos = (row, col)
    #        passable_cells = [TILE_BEAN, TILE_VACANCY, TILE_FIXED_PATH, TILE_EATMAN]
    #        if tiles[pos].symbol in passable_cells:
    #            cells_unvisited.append(tiles[pos])

    ## start walking the cells
    #random.shuffle(cells_unvisited)
    #cells_stack.append(cells_unvisited[0])

    ## when we still have cells that are unvisited
    #while len(cells_unvisited) > 0:

    #    # when we have non-zero stacks (means we have path to walk)
    #    while len(cells_stack) > 0:
    #        c_cell = cells_stack.pop()
    #        possible_path = get_possible_path(tiles, c_cell, cells_unvisited)
    #        for pp in possible_path:
    #            if pp not in cells_stack:
    #                cells_stack.append(pp)
    #        cells_unvisited.remove(c_cell)
    #        cells_visited.append(c_cell)

    #    # if the maze are not connected, we find the possible place to break the wall
    #    cells_possible_breakage = []
    #    if len(cells_unvisited) > 0:
    #        # the breakable ones
    #        for cell in cells_unvisited:
    #            breakpos =  find_possible_breakage(tiles, nrows, ncols, cell, cells_visited)
    #            if breakpos is not None:
    #                cells_possible_breakage.append((cell, breakpos))
    #        # The most separated ones 
    #        maxdist = 0
    #        for cell_1, breakpos_1 in cells_possible_breakage:
    #            for cell_2, breakpos_2 in cells_possible_breakage:
    #                if cell_1 is cell_2:
    #                    continue
    #                dist = (cell_1.pos[0]-cell_2.pos[0])**2 + (cell_1.pos[1]-cell_2.pos[1])**2
    #                if maxdist < dist:
    #                    maxdist = dist
    #                    pair = [(cell_1, breakpos_1), (cell_2, breakpos_2)]
    #        
    #        cell_1, breakpos_1 = pair[0]
    #        cell_2, breakpos_2 = pair[1]
    #        # break them
    #        tiles[breakpos_1].symbol = TILE_VACANCY
    #        tiles[breakpos_2].symbol = TILE_VACANCY
    #        print 'break', breakpos_1, breakpos_2
    #        # add the new vacancy to the unvisited list
    #        cells_unvisited.append(tiles[breakpos_1])
    #        cells_unvisited.append(tiles[breakpos_2])
    #        # add the cell_1 and cell_2 to the stack for new walk
    #        # TODO: Ideally, we wanna to make two breakages for each of the closed area. 
    #        # Thats why we choose to have cell_1 and cell_2. And starting walking from
    #        # cell_1 should reach cell_2.
    #        # However, if the unvisited part of the maze is still not connected by itself,
    #        # the two breakges will be two of the closed areas. And cell_1 won't reach
    #        # cell_2. So it has to be dealt differently. For now, we just add both cell_1
    #        # and cell_2 to the stack and save us the trouble for the case when 2 or more
    #        # closed areas are in the unvisited part, i.e. only one breakage will happen
    #        # for each of the closed area.
    #        cells_stack.append(cell_1)
    #        cells_stack.append(cell_2)


    # make the tunnel open
    tunnel_left = [
            '*****',
            '####*',
            '*****',
            '$####',
            '*****',
            '####*',
            '*****',
            ]
    tunnel_right = [
            '*****',
            '*####',
            '*****',
            '####$',
            '*****',
            '*####',
            '*****',
            ]
    for row in rowrange:
        for col in range(5):
            tiles[(row,col)].symbol = tunnel_left[row-rowrange[0]][col]
            tiles[(row,ncols-1-col)].symbol = tunnel_right[row-rowrange[0]][4-col]


    # print the maze
    #format_maze(tiles, nrows, ncols, printit=True)

    return format_maze(tiles, nrows, ncols)



if __name__ == '__main__':

    genmaze(21, 21)


