#!/usr/bin/env python


import os, sys, pygame
from pygame.locals import *
import pprint

SRCDIR                  = os.path.dirname(sys.argv[0])
TILE_WIDTH              = 24
TILE_HEIGHT             = 24

BACKGROUND_COLOR        = (  0,   0,   0)
WALL_FILL_COLOR         = (132,   0, 132)
WALL_EDGE_BRIGHT_COLOR  = (255, 206, 255)
WALL_EDGE_SHADOW_COLOR  = (255,   0, 255)


class map(object):

    def __init__(self):
        self.xsize = 600
        self.ysize = 600

    def loadLevel(self, ilevel):
        infile = open(os.path.join(SRCDIR, 'levels', str(ilevel)+'.dat'))
        self.leveldata = []
        for line in infile.readlines():
            line = line.strip()
            if line != '':
                fields = line.split(' ')
                if fields[0] == 'set':
                    # set variables
                    if fields[1] == 'backgroundcolor':
                        self.backgroundcolor = tuple([int(i) for i in fields[2:]])
                    elif fields[1] == 'walledgebrightcolor':
                        self.walledgebrightcolor = tuple([int(i) for i in fields[2:]])
                    elif fields[1] == 'walledgeshadowcolor':
                        self.walledgeshadowcolor = tuple([int(i) for i in fields[2:]])
                else: 
                    self.leveldata.append(line)

        self.nrows = len(self.leveldata)
        self.ncols = len(self.leveldata[0])
        for line in self.leveldata:
            assert len(line) == self.ncols

        pprint.pprint(self.leveldata)

        self.mapdata = []
        # now we need to analyze the map data
        for iy in range(self.nrows):
            mapline = []
            for ix in range(self.ncols):
                mapline.append(self.analyzeChar(ix, iy))
            self.mapdata.append(mapline)



    def draw(self, wallSurfs):
        x = 10
        y = 10

        for iy in range(self.nrows):

            mapline = self.mapdata[iy]
            for ix in range(self.ncols):
                tilekey = mapline[ix]

                if tilekey is None:
                    pass
                else:
                    DISPLAYSURF.blit(wallSurfs[tilekey], [x, y, TILE_WIDTH, TILE_HEIGHT])

                x += 24
            x = 10
            y += 24



    def analyzeChar(self, ix, iy):

        char = self.leveldata[iy][ix]
        # The chars surround it
        char_u = None if iy==0 else self.leveldata[iy-1][ix]
        char_d = None if iy==self.nrows-1 else self.leveldata[iy+1][ix]
        char_l = None if ix==0 else self.leveldata[iy][ix-1]
        char_r = None if ix==self.ncols-1 else self.leveldata[iy][ix+1]

        if char == '+':

            if char_r=='-' and char_d=='|':
                return 'corner-ul'

            if char_r=='-' and char_u=='|':
                return 'corner-ll'

            if char_l=='-' and char_d=='|':
                return 'corner-ur'

            if char_l=='-' and char_u=='|':
                return 'corner-lr'


        elif char == '-':
            if char_l in ['-','+'] and char_r in ['-','+']:
                return 'straight-hori'
            elif char_l in ['-','+']:
                return 'end-r'
            elif char_r in ['-','+']:
                return 'end-l'

        elif char == '|':
            if char_u in ['-','+'] and char_d in ['-','+']:
                return 'straight-vert'
            elif char_u in ['-','+']:
                return 'end-b'
            elif char_d in ['-','+']:
                return 'end-t'

        return None



        


class ghost(object):

    def __init__(self):
        pass


class eatman(object):
    '''
    class docs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.SPEED          = 3 # speed constant

        self.x              = 0
        self.y              = 0
        self.velocity       = 0 # current speed
        self.direction      = RIGHT # current direction
        self.nlifes         = 3

def loadWallImages():
    wallSurfs = {}
    keys = ['corner-ll', 'corner-lr', 'corner-ul', 'corner-ur', 
            'end-b', 'end-l', 'end-r', 'end-t', 
            'nub', 
            'straight-hori', 'straight-vert', 
            't-b', 't-l', 't-r', 't-t', 
            'x']
    for key in keys:
        wallSurfs[key] = pygame.image.load(os.path.join(SRCDIR,'tiles','wall-'+key+'.gif')).convert()

    return wallSurfs

def recolorWallImages(wallSurfs, backgroundcolor=None, walledgebrightcolor=None, walledgeshadowcolor=None):
    '''
    Re-color the wall tiles 
    '''
    for key in wallSurfs:

        for x in range(TILE_WIDTH):
            for y in range(TILE_HEIGHT):

                if backgroundcolor is not None \
                        and wallSurfs[key].get_at((x,y)) == WALL_FILL_COLOR:
                    wallSurfs[key].set_at((x,y), backgroundcolor)

                elif walledgebrightcolor is not None \
                        and wallSurfs[key].get_at((x,y)) == WALL_EDGE_BRIGHT_COLOR:
                    wallSurfs[key].set_at((x,y), walledgebrightcolor)

                elif walledgeshadowcolor is not None \
                        and wallSurfs[key].get_at((x,y)) == WALL_EDGE_SHADOW_COLOR:
                    wallSurfs[key].set_at((x,y), walledgeshadowcolor)
                    
    return wallSurfs



def main():
    pass



if __name__ == '__main__':

    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((900, 800))
    pygame.display.set_caption('EatMan')

    map = map()
    map.loadLevel(1)
    wallSurfs = loadWallImages()
    wallSurfs = recolorWallImages(wallSurfs, map.backgroundcolor, map.walledgebrightcolor, map.walledgeshadowcolor)


    DISPLAYSURF.fill(BACKGROUND_COLOR)
    #pygame.draw.line(DISPLAYSURF, map.walledgebrightcolor, (60, 60), (120, 60), 4)
    #pygame.draw.line(DISPLAYSURF, map.walledgeshadowcolor, (60, 90), (120, 90), 4)

    y = 10
    for key in wallSurfs:
        #DISPLAYSURF.blit(wallSurfs[key], [10, y, TILE_WIDTH, TILE_HEIGHT])
        y += 30

    map.draw(wallSurfs)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()










