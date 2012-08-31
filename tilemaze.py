#!/usr/bin/env python

J_SHAPE = 'j'
R_VLINE = '|' # right vertical line
B_HLINE = '_' # bottom horiz line
BR_DOT = '.' # bottom right dot

tile_templates = {}
tile_templates[J_SHAPE] = {}
tile_templates[R_VLINE] = {}
tile_templates[B_HLINE] = {}
tile_templates[BR_DOT] = {}

tile_templates[J_SHAPE]['fills'] = [
        ' *',
        '**' ]

tile_templates[R_VLINE]['fills'] = [
        ' *',
        ' *' ]

tile_templates[B_HLINE]['fills'] = [
        '  ',
        '**' ]

tile_templates[BR_DOT]['fills'] = [
        '  ',
        ' *' ]

tile_templates[J_SHAPE]['l_neighs'] = [B_HLINE, BR_DOT]
tile_templates[J_SHAPE]['r_neighs'] = [B_HLINE, BR_DOT]
tile_templates[J_SHAPE]['u_neighs'] = [R_VLINE, BR_DOT]
tile_templates[J_SHAPE]['d_neighs'] = [R_VLINE, B_HLINE, BR_DOT]

tile_templates[R_VLINE]['l_neighs'] = [R_VLINE, B_HLINE, BR_DOT]
tile_templates[R_VLINE]['r_neighs'] = [R_VLINE, B_HLINE, BR_DOT]
tile_templates[R_VLINE]['u_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[R_VLINE]['d_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]

tile_templates[B_HLINE]['l_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[B_HLINE]['r_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[B_HLINE]['u_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[B_HLINE]['d_neighs'] = [R_VLINE, B_HLINE, BR_DOT]

tile_templates[BR_DOT]['l_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[BR_DOT]['r_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[BR_DOT]['u_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]
tile_templates[BR_DOT]['d_neighs'] = [J_SHAPE, R_VLINE, B_HLINE, BR_DOT]

tiles = {}

class Tile(object):

    def __init__(self, shape):

        self.shape = shape
        self.fills = tile_templates[self.shape]['fills']
        self.l_neighs = tile_templates[self.shape]['l_neighs']
        self.r_neighs = tile_templates[self.shape]['r_neighs']
        self.u_neighs = tile_templates[self.shape]['u_neighs']
        self.d_neighs = tile_templates[self.shape]['d_neighs']

        self.pos = (0, 0)

    def get_path_pos(self):
        if self.shape == J_SHAPE:
            pos = [(0,0)]
        elif self.shape == R_VLINE:
            pos = [(0,0), (1,0)]
        elif self.shape == B_HLINE:
            pos = [(0,0), (0,1)]
        elif self.shape == BR_DOT:
            pos = [(0,0), (0,1), (1,0)]
        return pos

    def check_connect(self):
        u_pos = self.pos[0]-1, self.pos[1]
        d_pos = self.pos[0]+1, self.pos[1]
        l_pos = self.pos[0], self.pos[1]-1
        r_pos = self.pos[0], self.pos[1]+1

        all_pos = [u_pos, d_pos, l_pos, r_pos]
        for ii in range(len(all_pos)-1,-1,-1):
            pos = all_pos[ii]
            if pos[0] <= 0 or pos[0] >= nrows or pos[1] <= 0 or pos[1] >= ncols:
                all_pos.remove(pos)

        for pos in self.get_path_pos():
            nconnect = 0
            if pos == (0, 0):
                if self.fills[0][1] == ' ':
                    nconnect += 1
                if self.fills[1][0] == ' ':
                    nconnect += 1
                if u_pos in all_pos and tiles[u_pos].fills[1][0] == ' ':
                    nconnect += 1
                if l_pos in all_pos and tiles[l_pos].fills[0][1] == ' ':
                    nconnect += 1
            elif pos == (0, 1):
                if self.fills[0][0] == ' ':
                    nconnect += 1
                if self.fills[1][1] == ' ':
                    nconnect += 1
                if u_pos in all_pos and tiles[u_pos].fills[1][1] == ' ':
                    nconnect += 1
                if r_pos in all_pos and tiles[r_pos].fills[0][0] == ' ':
                    nconnect += 1
            elif pos == (1, 0):
                if self.fills[0][0] == ' ':
                    nconnect += 1
                if self.fills[1][1] == ' ':
                    nconnect += 1
                if d_pos in all_pos and tiles[d_pos].fills[0][0] == ' ':
                    nconnect += 1
                if l_pos in all_pos and tiles[l_pos].fills[1][1] == ' ':
                    nconnect += 1
            elif pos == (1, 1):
                if self.fills[0][1] == ' ':
                    nconnect += 1
                if self.fills[1][0] == ' ':
                    nconnect += 1
                if d_pos in all_pos and tiles[d_pos].fills[0][1] == ' ':
                    nconnect += 1
                if r_pos in all_pos and tiles[r_pos].fills[1][0] == ' ':
                    nconnect += 1

            if nconnect >= 2:
                # good
                pass
            else:
                # bad
                pass




def tilemaze(nrow, ncols):
    pass

if __name__ == '__main__':

    tilemaze()


