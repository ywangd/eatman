#!/usr/bin/env python


import os, sys, time, random, copy
import ConfigParser
import pygame
from pygame.locals import *
import pprint

FPS                     = 60

SRCDIR                  = os.path.abspath(os.path.dirname(sys.argv[0]))
TILE_WIDTH              = 24
TILE_HEIGHT             = 24

BACKGROUND_COLOR        = (  0,   0,   0)
WALL_FILL_COLOR         = (132,   0, 132)
WALL_BRIGHT_COLOR       = (255, 206, 255)
WALL_SHADOW_COLOR       = (255,   0, 255)
BEAN_FILL_COLOR         = (128,   0, 128)

STATIC                  = 's'
UP                      = 'u'
DOWN                    = 'd'
LEFT                    = 'l'
RIGHT                   = 'r'

EATMAN_IDLE             = 0
EATMAN_ANIMATE          = 1

GHOST_IDLE              = 0
GHOST_ANIMATE           = 1

L_WALL                  = '*'
L_EMPTY                 = ' '
L_BEAN                  = '.'
L_BEAN_BIG              = 'O'
L_EATMAN                = 'e'
L_GHOST_0               = '0'
L_GHOST_1               = '1'
L_GHOST_2               = '2'
L_GHOST_3               = '3'
L_GHOST_4               = '4'
L_GHOST_5               = '5'
L_GHOST_6               = '6'
L_GHOST_7               = '7'
L_GHOST_8               = '8'
L_GHOST_9               = '9'

#                           R    G    B
RED                     = (255,   0,   0, 255)
PINK                    = (255, 128, 255, 255)
CYAN                    = (128, 255, 255, 255)
ORANGE                  = (255, 128,   0, 255)
GRASS                   = ( 20, 175,  20, 255)
PURPLE                  = (128,   0, 255, 255)
BLUE                    = (50,   50, 255, 255)
WHITE                   = (248, 248, 248, 255)
BLACK                   = (  0,   0,   0, 255)
GRAY                    = (185, 185, 185, 255)
YELLOW                  = (255, 255,   0, 255)

class Config(object):
    '''
    The class to store informations about the game configurations.
    '''

    def __init__(self):
        parser = ConfigParser.ConfigParser()
        infile = os.path.join(SRCDIR, 'config.ini')
        parser.read(infile)

        # Populate the parameters
        func = {'s': parser.get, 'i': parser.getint, 'f': parser.getfloat, 'b': parser.getboolean}
        self.pars = {}
        for section in parser.sections():
            self.pars[section] = {}
            for option in parser.options(section):
                self.pars[section][option] = func[option[0]](section, option)

    def get(self, section, option):
        return self.pars[section][option]


class Resource(object):
    '''
    The class to store common game resources, including tiles, sounds, texts etc.
    '''

    def __init__(self):
        pass

    def load_tiles(self, level=None):
        self.tiles = {}
        files = os.listdir(os.path.join(SRCDIR,'tiles'))
        for filename in files:
            if filename[-3:] == 'gif':
                key = filename[:-4]
                self.tiles[key] = pygame.image.load(os.path.join(SRCDIR,'tiles',filename)).convert()

        if level is not None:
            self.recolor_tiles(level)


    def load_sounds(self):
        self.sounds = {}
        files = os.listdir(os.path.join(SRCDIR,'sounds'))
        for filename in files:
            if filename[-3:] == 'wav':
                key = filename[:-4]
                self.sounds[key] = pygame.mixer.Sound(os.path.join(SRCDIR,'sounds',filename))


    def load_fires(self):
        self.fires = {}
        files = os.listdir(os.path.join(SRCDIR,'sprites'))
        for filename in files:
            if filename[0:4] == 'fire' and filename[-3:] == 'gif':
                key = filename[:-4]
                self.fires[key] = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()


    def recolor_tiles(self, level):
        '''
        Re-color the tiles according to the settings in level file.
        '''
        for key in self.tiles:

            if key[0:4] == 'wall':

                for x in range(TILE_WIDTH):
                    for y in range(TILE_HEIGHT):

                        if self.tiles[key].get_at((x,y))==WALL_FILL_COLOR:
                            self.tiles[key].set_at((x,y), level.bgcolor)

                        elif self.tiles[key].get_at((x,y)) == WALL_BRIGHT_COLOR:
                            self.tiles[key].set_at((x,y), level.wallbrightcolor)

                        elif self.tiles[key].get_at((x,y)) == WALL_SHADOW_COLOR:
                            self.tiles[key].set_at((x,y), level.wallshadowcolor)
                    
            elif key[0:4] == 'bean':

                for x in range(TILE_WIDTH):
                    for y in range(TILE_HEIGHT):

                        if self.tiles[key].get_at((x,y))==BEAN_FILL_COLOR:
                            self.tiles[key].set_at((x,y), level.beancolor)

class Node():
    
    def __init__ (self):
        self.g = -1 # movement cost to move from previous node to this one (usually +10)
        self.h = -1 # estimated movement cost to move from this node to the ending node (remaining horizontal and vertical steps * 10)
        self.f = -1 # total movement cost of this node (= g + h)
        # parent node - used to trace path back to the starting node at the end
        self.parent = (-1, -1)
        # node type - 0 for empty space, 1 for wall (optionally, 2 for starting node and 3 for end)
        self.type = -1

class Pathfinder(object):

    NODE_TYPE_NOT_VISITED   = 0
    NODE_TYPE_BLOCKED       = 1
    NODE_TYPE_START         = 2
    NODE_TYPE_END           = 3
    NODE_TYPE_CURRENT       = 4

    def __init__ (self):
        # use the unfold( (row, col) ) function to convert a 2D coordinate pair
        # into a 1D index to use with this array.
        self.map = {}
        self.size = (-1, -1) # rows by columns
        
        self.pathChainRev = ''
        self.pathChain = ''
                
        # starting and ending nodes
        self.spos = (-1, -1)
        self.epos = (-1, -1)
        
        # current node (used by algorithm)
        self.current = (-1, -1)
        
        # open and closed lists of nodes to consider (used by algorithm)
        self.openlist = []
        self.closelist = []
        
        # used in algorithm (adjacent neighbors path finder is allowed to consider)
        self.neighborSet = [ (0, -1), (0, 1), (-1, 0), (1, 0) ]


    def randpath(self, level, ghost, eatman):
        moveto = [UP, DOWN, LEFT, RIGHT]
        if ghost.moved_from == UP or (not is_valid_position(level, ghost, yoffset=-1)):
            moveto.remove(UP)
        if ghost.moved_from == DOWN or (not is_valid_position(level, ghost, yoffset=1)):
            moveto.remove(DOWN)
        if ghost.moved_from == LEFT or (not is_valid_position(level, ghost, xoffset=-1)):
            moveto.remove(LEFT)
        if ghost.moved_from == RIGHT or (not is_valid_position(level, ghost, xoffset=1)):
            moveto.remove(RIGHT)

        if len(moveto) == 0:
            return ghost.moved_from

        return random.choice(moveto)


    def findpath(self, level, entity, target):

        self.clear_temp_vars()
        
        # (row, col) tuples
        (x, y) = xy_to_uv((entity.x, entity.y))
        self.spos = (y, x)
        entity.seekerTargetX, entity.seekerTargetY = xy_to_uv((target.x, target.y))
        self.epos = entity.seekerTargetY, entity.seekerTargetX

        # add start node to open list
        self.add_to_openlist( self.spos )
        self.setG ( self.spos, 0 )
        self.setH ( self.spos, 0 )
        self.setF ( self.spos, 0 )
        
        doContinue = True
        
        while (doContinue == True):
        
            thisLowestFNode = self.get_lowest_F_node()

            if not thisLowestFNode == self.epos and not thisLowestFNode == False:
                self.current = thisLowestFNode
                self.remove_from_openlist( self.current )
                self.add_to_closelist( self.current )
                
                for offset in self.neighborSet:
                    thisNeighbor = (self.current[0] + offset[0], self.current[1] + offset[1])
                    
                    if not thisNeighbor[0] < 0 and \
                            not thisNeighbor[1] < 0 and \
                            not thisNeighbor[0] > self.size[0] - 1 and \
                                    not thisNeighbor[1] > self.size[1] - 1 and \
                                    not self.get_type( thisNeighbor ) == 1:
                        cost = self.getG( self.current ) + 10
                        
                        if self.is_in_openlist( thisNeighbor ) and cost < self.getG( thisNeighbor ):
                            self.remove_from_openlist( thisNeighbor )
                            
                        if not self.is_in_openlist( thisNeighbor ) and not self.is_in_closelist( thisNeighbor ):
                            self.add_to_openlist( thisNeighbor )
                            self.setG( thisNeighbor, cost )
                            self.calcH( thisNeighbor )
                            self.calcF( thisNeighbor )
                            self.set_parent( thisNeighbor, self.current )
            else:
                doContinue = False
                        
        if thisLowestFNode == False:
            return False
                        
        # reconstruct path
        self.current = self.epos
        while not self.current == self.spos:
            # build a string representation of the path 
            if self.current[1] > self.get_parent(self.current)[1]:
                self.pathChainRev += RIGHT
            elif self.current[1] < self.get_parent(self.current)[1]:
                self.pathChainRev += LEFT
            elif self.current[0] > self.get_parent(self.current)[0]:
                self.pathChainRev += DOWN
            elif self.current[0] < self.get_parent(self.current)[0]:
                self.pathChainRev += UP
            self.current = self.get_parent(self.current)
            self.set_type( self.current, Pathfinder.NODE_TYPE_CURRENT)
            
        # because pathChainRev was constructed in reverse order, it needs to be reversed!
        for i in range(len(self.pathChainRev) - 1, -1, -1):
            self.pathChain += self.pathChainRev[i]
        
        # set start and ending positions for future reference
        self.set_type( self.spos, Pathfinder.NODE_TYPE_START)
        self.set_type( self.epos, Pathfinder.NODE_TYPE_END)
        
        return self.pathChain

    def init_map(self, level):
        self.map = {}
        self.size = (level.nrows, level.ncols)

        # initialize path_finder map to a 2D array of empty nodes
        for row in range(0, self.size[0], 1):
            for col in range(0, self.size[1], 1):

                self.set_node( (row, col), Node() )

                if level.data[row][col] == L_WALL:
                    self.set_type((row, col), Pathfinder.NODE_TYPE_BLOCKED)
                else:
                    self.set_type((row, col), Pathfinder.NODE_TYPE_NOT_VISITED)


    def unfold (self, (row, col)):
        # this function converts a 2D array coordinate pair (row, col)
        # to a 1D-array index, for the object's 1D map array.
        return (row * self.size[1]) + col
    
    def set_node (self, (row, col), newNode):
        # sets the value of a particular map cell (usually refers to a node object)
        self.map[ self.unfold((row, col)) ] = newNode
        
    def get_type (self, (row, col)):
        return self.map[ self.unfold((row, col)) ].type
        
    def set_type (self, (row, col), theType):
        self.map[ self.unfold((row, col)) ].type = theType

    def getF (self, (row, col)):
        return self.map[ self.unfold((row, col)) ].f

    def getG (self, (row, col)):
        return self.map[ self.unfold((row, col)) ].g
    
    def getH (self, (row, col)):
        return self.map[ self.unfold((row, col)) ].h
        
    def setG (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ].g = newValue

    def setH (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ].h = newValue
        
    def setF (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ].f = newValue
        
    def calcH (self, (row, col)):
        self.map[ self.unfold((row, col)) ].h = abs(row - self.epos[0]) + abs(col - self.epos[0])
        
    def calcF (self, (row, col)):
        unfoldIndex = self.unfold((row, col))
        self.map[unfoldIndex].f = self.map[unfoldIndex].g + self.map[unfoldIndex].h
    
    def add_to_openlist (self, (row, col) ):
        self.openlist.append( (row, col) )
        
    def remove_from_openlist (self, (row, col) ):
        self.openlist.remove( (row, col) )
        
    def is_in_openlist (self, (row, col) ):
        if self.openlist.count( (row, col) ) > 0:
            return True
        else:
            return False
        
    def get_lowest_F_node (self):
        lowestValue = 1000 # start arbitrarily high
        lowestPair = (-1, -1)
        
        for iOrderedPair in self.openlist:
            if self.getF( iOrderedPair ) < lowestValue:
                lowestValue = self.getF( iOrderedPair )
                lowestPair = iOrderedPair
        
        if not lowestPair == (-1, -1):
            return lowestPair
        else:
            return False
        
    def add_to_closelist (self, (row, col) ):
        self.closelist.append( (row, col) )
        
    def is_in_closelist (self, (row, col) ):
        if self.closelist.count( (row, col) ) > 0:
            return True
        else:
            return False

    def set_parent (self, (row, col), (parentRow, parentCol) ):
        self.map[ self.unfold((row, col)) ].parent = (parentRow, parentCol)

    def get_parent (self, (row, col) ):
        return self.map[ self.unfold((row, col)) ].parent
        
    def clear_temp_vars (self):
        # this resets variables needed for a search (but preserves the same map / maze)
        self.pathChainRev = ''
        self.pathChain = ''
        self.current = (-1, -1)
        self.openlist = []
        self.closelist = []


#################################################################################
# The global variables

config = Config() # Read the config.ini file
resource = Resource()
pathfinder = Pathfinder()

#################################################################################

class Level(object):

    def __init__(self):
        self.bgcolor = (0, 0, 0)
        self.beancolor = (255, 255, 255)
        self.wallbrightcolor = (0, 0, 255)
        self.wallshadowcolor = (0, 0, 255)

        self.nbeans = 0
        self.idx_beansound = 0

        self.eatman_params = {}

        self.nghosts = 0
        self.ghost_params = {}

    def load(self, ilevel):
        infile = open(os.path.join(SRCDIR, 'levels', str(ilevel)+'.dat'))
        self.data = []
        for line in infile.readlines():
            line = line.strip()
            if line != '':
                fields = line.split(' ')

                if fields[0] == 'set': # set variables
                    if fields[1] == 'bgcolor':
                        self.bgcolor = tuple([int(i) for i in fields[2:]])
                    elif fields[1] == 'beancolor':
                        self.beancolor = tuple([int(i) for i in fields[2:]])
                    elif fields[1] == 'wallbrightcolor':
                        self.wallbrightcolor = tuple([int(i) for i in fields[2:]])
                    elif fields[1] == 'wallshadowcolor':
                        self.wallshadowcolor = tuple([int(i) for i in fields[2:]])

                elif fields[0] == 'ghost': # ghost parameters
                    idx = int(fields[1])
                    self.ghost_params[idx] = {}
                    for pair in fields[2:]:
                        attr, val = pair.split('=')
                        if attr == 'color':
                            self.ghost_params[idx][attr] = globals()[val]
                        elif attr == 'fast': # factor of speed boost 1-infinity
                            self.ghost_params[idx][attr] = float(val)
                        elif attr == 'seeker': # chance to seek (0-100)
                            self.ghost_params[idx][attr] = int(val)
                        elif attr == 'chilling': # factor of player speed reduction 1-infinity
                            self.ghost_params[idx][attr] = float(val)
                        elif attr == 'molten': # chance to leave a fire on path
                            self.ghost_params[idx][attr] = int(val)

                else: # the ascii level content
                    # All the space are replaced by dot that represents a bean
                    self.data.append(list(line.replace(L_EMPTY, L_BEAN)))

        self.nrows = len(self.data)
        self.ncols = len(self.data[0])
        for line in self.data:
            assert len(line) == self.ncols

    def create_map(self):
        '''
        Analyze the ascii level data and create the map
        '''
        self.map = []
        for iy in range(self.nrows):
            mapline = []
            for ix in range(self.ncols):
                tilename = self.get_tile_name(ix, iy)
                mapline.append(tilename)
            self.map.append(mapline)


    def get_tile_name(self, ix, iy):
        '''
        Analyze a character to determine its tile name
        '''
        char = self.data[iy][ix]
        # The chars surround it
        char_u = None if iy==0 else self.data[iy-1][ix]
        char_d = None if iy==self.nrows-1 else self.data[iy+1][ix]
        char_l = None if ix==0 else self.data[iy][ix-1]
        char_r = None if ix==self.ncols-1 else self.data[iy][ix+1]

        if char == L_EMPTY:
            return None

        elif char == L_WALL: # walls

            if char_u==L_WALL and char_d==L_WALL and char_l==L_WALL and char_r==L_WALL:
                return 'wall-x'

            if char_u==L_WALL and char_d==L_WALL and char_l==L_WALL:
                return 'wall-t-r'

            if char_u==L_WALL and char_d==L_WALL and char_r==L_WALL:
                return 'wall-t-l'

            if char_u==L_WALL and char_l==L_WALL and char_r==L_WALL:
                return 'wall-t-b'

            if char_d==L_WALL and char_l==L_WALL and char_r==L_WALL:
                return 'wall-t-t'

            if char_r==L_WALL and char_d==L_WALL:
                return 'wall-corner-ul'

            if char_r==L_WALL and char_u==L_WALL:
                return 'wall-corner-ll'

            if char_l==L_WALL and char_d==L_WALL:
                return 'wall-corner-ur'

            if char_l==L_WALL and char_u==L_WALL:
                return 'wall-corner-lr'

            if char_l==L_WALL and char_r==L_WALL:
                return 'wall-straight-hori'

            if char_u==L_WALL and char_d==L_WALL:
                return 'wall-straight-vert'

            if char_l==L_WALL: 
                return 'wall-end-r'

            if char_r==L_WALL:
                return 'wall-end-l'

            if char_u==L_WALL:
                return 'wall-end-b'

            if char_d==L_WALL:
                return 'wall-end-t'

            return 'wall-nub'

        elif char == L_EATMAN:
            self.eatman_params['xy'] = (ix, iy)
            return None

        elif char in [L_GHOST_0, L_GHOST_1, L_GHOST_2, L_GHOST_3, L_GHOST_4, 
                L_GHOST_5, L_GHOST_6, L_GHOST_7, L_GHOST_8, L_GHOST_9]:
            self.nghosts += 1
            self.ghost_params[int(char)]['xy'] = (ix, iy)
            return None

        elif char == L_BEAN_BIG:
            self.nbeans += 1
            return 'bean-big'

        elif char == L_BEAN:
            self.nbeans += 1
            return 'bean'

        return None


    def draw(self, DISPLAYSURF):
        x = 10
        y = 10

        for iy in range(self.nrows):

            mapline = self.map[iy]
            for ix in range(self.ncols):
                tilekey = mapline[ix]

                if tilekey is not None:
                    DISPLAYSURF.blit(resource.tiles[tilekey], [x, y, TILE_WIDTH, TILE_HEIGHT])

                x += 24

            x = 10
            y += 24



class Fire(object):

    def __init__(self, (u, v)):
        self.u, self.v = u, v
        self.stime = time.time()

        self.lastAnimTime = time.time()
        self.duration = config.get('Fire','fduration') # last for how many seconds
        self.animFreq = config.get('Fire','fanimatefrequency')
        self.idx_frame = 0
        self.frame_sequence = [1,2,3,4,5,6,7,8,1]

    def animate(self, DISPLAYSURF):
        x, y = uv_to_xy((self.u, self.v))
        rect = [x, y, TILE_WIDTH, TILE_HEIGHT]
        id = self.frame_sequence[self.idx_frame]
        DISPLAYSURF.blit(resource.fires['fire-'+str(id)], rect)
        if time.time()-self.lastAnimTime > self.animFreq:
            self.idx_frame += 1
            self.lastAnimTime = time.time()
            if self.idx_frame >= len(self.frame_sequence):
                self.idx_frame = 0

    def is_expired(self):
        if time.time()-self.stime > self.duration:
            return True
        else:
            return False



        


class Ghost(object):

    # When a move strategy is in effect, e.g. seeker, how many
    # steps (grid cells) does the ghost move before it
    # rolls for the next move strategy
    BASE_STEP_MOVE_CYCLE = 10    # 10 cells 

    PUPIL_LR = (8, 9)
    PUPIL_LL = (5, 9)
    PUPIL_UR = (8, 6)
    PUPIL_UL = (5, 6)

    def __init__(self, idx, level, eatman):
        self.state = GHOST_IDLE
        self.speed = 3
        self.animFreq = config.get('Ghost','fanimatefrequency')
        self.speed = config.get('Ghost','ispeed')
        self.pathway = ''

        self.max_step_move_cycle = Ghost.BASE_STEP_MOVE_CYCLE + random.randint(-3,3)
        self.nsteps_move_cycle = 0
        self.move_strategy = ''

        self.x, self.y = uv_to_xy(level.ghost_params[idx]['xy'])
        self.color = level.ghost_params[idx]['color']

        if level.ghost_params[idx].has_key('fast'):
            self.animFreq /= level.ghost_params[idx]['fast']

        if level.ghost_params[idx].has_key('seeker'):
            self.seekerPercent = level.ghost_params[idx]['seeker']
        else:
            self.seekerPercent = 0

        if level.ghost_params[idx].has_key('molten'):
            self.moltenPercent = level.ghost_params[idx]['molten']
        else:
            self.moltenPercent = 0

        # chilling rate, time started, duration
        if level.ghost_params[idx].has_key('chilling'):
            eatman.animFreq_factors['ghost-'+str(idx)] = (level.ghost_params[idx]['chilling'], \
                    time.time(), -1)


        self.pupil_color = BLACK
        self.pupil_pos = Ghost.PUPIL_LR

        self.direction = STATIC
        self.moved_from = None

        self.load_sprites()
        self.idx_frame = 0
        self.lastAnimTime = time.time()

        self.seekerTargetX = 0
        self.seekerTargetY = 0

    def load_sprites(self):
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        self.frames = []
        for idx_frame in range(self.nframes):

            filename = os.path.join(SRCDIR,'sprites','ghost-'+str(frame_sequence[idx_frame])+'.gif')
            img = pygame.image.load(filename).convert()

            # modify the color
            for x in range(TILE_WIDTH):
                for y in range(TILE_HEIGHT):
                    if img.get_at((x,y)) == RED:
                        img.set_at((x,y), self.color)

            # remove the eyes, will be drawn dynamically
            for y in range(6,12):
                for x in [5,6,8,9]:
                    img.set_at((x,y), WHITE)
                    img.set_at((x+9,y), WHITE)

            self.frames.append(img)


    def draw(self, DISPLAYSURF, eatman):

        img = self.frames[self.idx_frame].copy()

        # set the eye ball position
        if eatman.x > self.x and eatman.y > self.y:
            self.pupil_pos = Ghost.PUPIL_LR
        elif eatman.x < self.x and eatman.y > self.y:
            self.pupil_pos = Ghost.PUPIL_LL
        elif eatman.x > self.x and eatman.y < self.y:
            self.pupil_pos = Ghost.PUPIL_UR
        elif eatman.x < self.x and eatman.y < self.y:
            self.pupil_pos = Ghost.PUPIL_UL
        else:
            self.pupil_pos = Ghost.PUPIL_LL

        for y in range(self.pupil_pos[1], self.pupil_pos[1]+3):
            for x in range(self.pupil_pos[0], self.pupil_pos[0]+2):
                img.set_at((x,y), self.pupil_color)
                img.set_at((x+9,y), self.pupil_color)
                
        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]
        DISPLAYSURF.blit(img, rect)


    def make_move(self, level, eatman, fires):

        # If it is in middle of an animation, keep doint it till the cycle is done.
        if self.state == GHOST_ANIMATE and time.time()-self.lastAnimTime>self.animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.state = GHOST_IDLE
                self.nsteps_move_cycle += 1
                self.moved_from = get_opposite_direction(self.direction)
                # drop fire
                if self.moltenPercent>0 and len(fires)<100 and random.randint(1,100)<self.moltenPercent:
                    fires.append(Fire(xy_to_uv((self.x, self.y))))
            else:
                if self.direction == DOWN:
                    self.y += self.speed
                elif self.direction == UP:
                    self.y -= self.speed
                elif self.direction == LEFT:
                    self.x -= self.speed
                elif self.direction == RIGHT:
                    self.x += self.speed
                self.lastAnimTime = time.time()

        # If it is not animating, we need to figure out where to go for the next animation cycle
        if self.state == GHOST_IDLE:

            if len(self.pathway) > 0: # if there is a existing pathway
                # re-roll the strategy if it is expired
                if self.nsteps_move_cycle > self.max_step_move_cycle:
                    self.nsteps_move_cycle = 0
                    if random.randint(1,100) <= self.seekerPercent:
                        self.move_strategy = 'seeker'
                        self.pathway = pathfinder.findpath(level, self, eatman)
                    else:
                        self.move_strategy = 'random'
                        self.pathway = pathfinder.randpath(level, self, eatman)

                if self.move_strategy == 'seeker':
                    u, v = xy_to_uv((eatman.x, eatman.y))
                    if self.seekerTargetX == u or self.seekerTargetY == v \
                            or ((self.seekerTargetX-u)**2+(self.seekerTargetY-v)**2)<18:
                        pass
                    else:
                        self.pathway = pathfinder.findpath(level, self, eatman)

            else: # if no existing pathway
                if self.nsteps_move_cycle > self.max_step_move_cycle or self.move_strategy == '':
                    self.nsteps_move_cycle = 0
                    # re-roll the strategy
                    if random.randint(1,100) <= self.seekerPercent: # seek it
                        self.move_strategy = 'seeker'
                        self.pathway = pathfinder.findpath(level, self, eatman)
                    else: # random path
                        self.move_strategy = 'random'
                        self.pathway = pathfinder.randpath(level, self, eatman)
                else:
                    if self.move_strategy == 'seeker':
                        self.pathway = pathfinder.findpath(level, self, eatman)
                    elif self.move_strategy == 'random':
                        self.pathway = pathfinder.randpath(level, self, eatman)

            # now follow the pathway
            self.follow_pathway()


    def follow_pathway(self):
        if len(self.pathway) > 0:
            moveto = self.pathway[0]
            self.pathway = self.pathway[1:]
            self.state = GHOST_ANIMATE
            self.direction = moveto
        else:
            self.state = GHOST_IDLE
            self.direction = STATIC


class Eatman(object):
    '''
    The Eatman class for managing the Player.
    '''

    def __init__(self, level):

        self.state          = EATMAN_IDLE
        self.direction      = STATIC
        self.nlifes         = 3

        self.x, self.y = uv_to_xy(level.eatman_params['xy'])

        self.animFreq = config.get('Eatman', 'fanimatefrequency')
        self.speed = config.get('Eatman','ispeed')

        self.animFreq_factors = {}

        self.load_sprites()
        self.idx_frame      = 0
        self.lastAnimTime = time.time()


    def load_sprites(self):
        directions = [DOWN, LEFT, RIGHT, UP] 
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        self.frames = {}
        for direc in directions:
            self.frames[direc] = []
            for idx_frame in range(self.nframes):
                filename = os.path.join(SRCDIR,'sprites','eatman-'+direc+'-'+str(frame_sequence[idx_frame])+'.gif')
                self.frames[direc].append(pygame.image.load(filename).convert())

        self.frames[STATIC] = pygame.image.load(os.path.join(SRCDIR,'sprites','eatman.gif')).convert()


    def make_move(self):

        # modify the animation frequency by any buff/debuff
        animFreq = self.animFreq
        for key in self.animFreq_factors:
            vals = self.animFreq_factors[key]
            if vals[2] < 0 or time.time()-vals[1]<vals[2]:
                animFreq *= vals[0]
            else:
                del(self.animFreq_factors[key])

        # Only animate the player if it is in animate state and with proper frequency
        if self.state == EATMAN_ANIMATE and time.time()-self.lastAnimTime>animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.state = EATMAN_IDLE
            else:
                if self.direction == DOWN:
                    self.y += self.speed
                elif self.direction == UP:
                    self.y -= self.speed
                elif self.direction == LEFT:
                    self.x -= self.speed
                elif self.direction == RIGHT:
                    self.x += self.speed
                self.lastAnimTime = time.time()


    def draw(self, DISPLAYSURF):

        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]

        if self.direction == STATIC:
            DISPLAYSURF.blit(self.frames[self.direction], rect)
        else:
            DISPLAYSURF.blit(self.frames[self.direction][self.idx_frame], rect)



# x, y is column, row
def xy_to_uv((x, y)):
    '''
    Convert the screen pixel coordinates to the board grid coordinates.
    The results are rounded to the nearest integers.
    '''
    return (int(round((x-config.get('Game','ixmargin'))*1.0/TILE_WIDTH)),
            int(round((y-config.get('Game','iymargin'))*1.0/TILE_HEIGHT)))

def uv_to_xy((u, v)):
    '''
    Convert the board grid coordinates to screen pixel coordinates
    '''
    return (config.get('Game','ixmargin')+u*TILE_WIDTH,
            config.get('Game','iymargin')+v*TILE_HEIGHT)

def get_opposite_direction(direction):
    if direction == UP:
        return DOWN
    if direction == DOWN:
        return UP
    if direction == LEFT:
        return RIGHT
    if direction == RIGHT:
        return LEFT



def is_valid_position(level, entity, xoffset=0, yoffset=0):

    x, y = xy_to_uv((entity.x, entity.y))
    x += xoffset
    y += yoffset

    if level.data[y][x] not in [L_WALL,]:
        return True
    else:
        return False


def check_hit(level, eatman):
    x, y = xy_to_uv((eatman.x, eatman.y))

    # Check if a bean is hit
    if level.data[y][x] == L_BEAN:
        level.data[y][x] = L_EMPTY
        level.map[y][x] = level.get_tile_name(x, y)
        level.nbeans -= 1
        resource.sounds['bean-'+str(level.idx_beansound)].play()
        level.idx_beansound += 1
        if level.idx_beansound >=2:
            level.idx_beansound = 0
        if level.nbeans == 0:
            # WIN
            pass

    if level.data[y][x] == L_BEAN_BIG:
        level.data[y][x] = L_EMPTY
        level.map[y][x] = level.get_tile_name(x, y)
        level.nbeans -= 1
        resource.sounds['bean-big'].play()
        if level.nbeans == 0:
            # WIN
            pass



def main():

    pygame.init()

    DISPLAYSURF = pygame.display.set_mode((900, 800))
    pygame.display.set_caption('EatMan')

    clock_fps = pygame.time.Clock()

    level = Level()
    level.load(1)
    level.create_map()

    pathfinder.init_map(level)

    # recolor the tiles according to the level requirement
    resource.load_tiles(level)
    resource.load_sounds()
    resource.load_fires()

    eatman = Eatman(level)

    ghosts = []
    for i in range(level.nghosts):
        ghosts.append(Ghost(i, level, eatman))

    fires = []

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:

                if event.key == K_UP:
                    moveDown = False
                    moveUp = True

                elif event.key == K_DOWN:
                    moveUp = False
                    moveDown = True

                elif event.key == K_LEFT:
                    moveRight = False
                    moveLeft = True

                elif event.key == K_RIGHT:
                    moveLeft = False
                    moveRight = True

            elif event.type == KEYUP:
                if event.key == K_LEFT:
                    moveLeft = False
                elif event.key == K_RIGHT:
                    moveRight = False
                elif event.key == K_UP:
                    moveUp = False
                elif event.key == K_DOWN:
                    moveDown = False

                elif event.key == K_ESCAPE:
                    # TODO: game menu
                    pass 

        # Always change the facing direction when eatman is idle.
        # But only animate it if there is valid space to move.
        if (moveUp or moveDown or moveLeft or moveRight) and eatman.state == EATMAN_IDLE:
            if moveUp: 
                eatman.direction = UP 
                if is_valid_position(level, eatman, yoffset=-1):
                    eatman.state = EATMAN_ANIMATE
            elif moveDown: 
                eatman.direction = DOWN
                if is_valid_position(level, eatman, yoffset=1):
                    eatman.state = EATMAN_ANIMATE
            elif moveLeft:
                eatman.direction = LEFT
                if is_valid_position(level, eatman, xoffset=-1):
                    eatman.state = EATMAN_ANIMATE
            elif moveRight:
                eatman.direction = RIGHT
                if is_valid_position(level, eatman, xoffset=1):
                    eatman.state = EATMAN_ANIMATE

        eatman.make_move()
        for ghost in ghosts:
            ghost.make_move(level, eatman, fires)

        DISPLAYSURF.fill(BACKGROUND_COLOR)

        level.draw(DISPLAYSURF)

        for id in range(len(fires)-1, -1, -1):
            if fires[id].is_expired():
                del(fires[id]) 
            else:
                fires[id].animate(DISPLAYSURF)

        eatman.draw(DISPLAYSURF)

        for ghost in ghosts:
            ghost.draw(DISPLAYSURF, eatman)

        


        pygame.display.update()

        check_hit(level, eatman)

        #clock_fps.tick(FPS)



if __name__ == '__main__':

    main()





