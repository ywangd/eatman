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



#################################################################################
# The global variables

config = Config() # Read the config.ini file
resource = Resource()

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



        


class Ghost(object):

    PUPIL_LR = (8, 9)
    PUPIL_LL = (5, 9)
    PUPIL_UR = (8, 6)
    PUPIL_UL = (5, 6)

    def __init__(self, level, idx):
        self.state = GHOST_IDLE
        self.speed = 3
        self.animFreq = config.get('Ghost','fanimatefrequency')
        self.speed = config.get('Ghost','ispeed')

        self.color = level.ghost_params[idx]['color']
        self.x, self.y = uv_to_xy(level.ghost_params[idx]['xy'])

        self.pupil_color = BLACK
        self.pupil_pos = Ghost.PUPIL_LR

        self.direction = STATIC

        self.load_sprite()
        self.idx_frame = 0
        self.lastAnimTime = time.time()

    def load_sprite(self):
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        self.frames = []
        for idx_frame in range(self.nframes):

            filename = os.path.join(SRCDIR,'sprite','ghost-'+str(frame_sequence[idx_frame])+'.gif')
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


    def draw(self, DISPLAYSURF):

        img = self.frames[self.idx_frame].copy()

        for y in range(self.pupil_pos[1], self.pupil_pos[1]+3):
            for x in range(self.pupil_pos[0], self.pupil_pos[0]+2):
                img.set_at((x,y), self.pupil_color)
                img.set_at((x+9,y), self.pupil_color)
                
        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]
        DISPLAYSURF.blit(img, rect)


    def make_move(self):
        pass




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

        self.load_sprite()
        self.idx_frame      = 0
        self.lastAnimTime = time.time()


    def load_sprite(self):
        directions = [DOWN, LEFT, RIGHT, UP] 
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        self.frames = {}
        for direc in directions:
            self.frames[direc] = []
            for idx_frame in range(self.nframes):
                filename = os.path.join(SRCDIR,'sprite','eatman-'+direc+'-'+str(frame_sequence[idx_frame])+'.gif')
                self.frames[direc].append(pygame.image.load(filename).convert())

        self.frames[STATIC] = pygame.image.load(os.path.join(SRCDIR,'sprite','eatman.gif')).convert()

    def make_move(self):

        if self.state == EATMAN_ANIMATE and time.time()-self.lastAnimTime>self.animFreq:
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


def is_valid_position(level, eatman, xoffset=0, yoffset=0):

    x, y = xy_to_uv((eatman.x, eatman.y))
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

    # recolor the tiles according to the level requirement
    resource.load_tiles(level)
    resource.load_sounds()

    eatman = Eatman(level)

    ghosts = []
    for i in range(level.nghosts):
        ghosts.append(Ghost(level, i))

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

        DISPLAYSURF.fill(BACKGROUND_COLOR)
        level.draw(DISPLAYSURF)
        eatman.draw(DISPLAYSURF)
        for ghost in ghosts:
            ghost.draw(DISPLAYSURF)
        pygame.display.update()

        check_hit(level, eatman)

        #clock_fps.tick(FPS)



if __name__ == '__main__':

    main()





