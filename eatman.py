#!/usr/bin/env python


import os, sys, time, random, pygame
import ConfigParser
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

L_WALL                  = '*'
L_EMPTY                 = ' '
L_BEAN                  = '.'
L_BEAN_BIG              = 'O'
L_EATMAN                = 'e'
L_GHOST_W               = 'w'
L_GHOST_X               = 'x'
L_GHOST_Y               = 'y'
L_GHOST_Z               = 'z'


class Config(object):

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


# Read the config.ini file
config = Config() 


class Level(object):

    def __init__(self):
        self.bgcolor = (0, 0, 0)
        self.beancolor = (255, 255, 255)
        self.wallbrightcolor = (0, 0, 255)
        self.wallshadowcolor = (0, 0, 255)

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

        if char == L_WALL: # walls

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
            self.eatman_xy = (ix, iy)
            return 'eatman'

        elif char == L_GHOST_W:
            return 'ghost-w'

        elif char == L_GHOST_X:
            return 'ghost-x'

        elif char == L_GHOST_Y:
            return 'ghost-y'

        elif char == L_GHOST_Z:
            return 'ghost-z'

        elif char == L_BEAN_BIG:
            return 'bean-big'

        elif char == L_BEAN:
            return 'bean'

        elif char == L_EMPTY:
            return None

        return None


    def draw(self, DISPLAYSURF, resource):
        x = 10
        y = 10

        for iy in range(self.nrows):

            mapline = self.map[iy]
            for ix in range(self.ncols):
                tilekey = mapline[ix]

                if tilekey is not None and tilekey not in ['eatman']:
                    DISPLAYSURF.blit(resource.tiles[tilekey], [x, y, TILE_WIDTH, TILE_HEIGHT])

                x += 24

            x = 10
            y += 24



        


class Ghost(object):

    def __init__(self):
        pass


class Eatman(object):
    '''
    class docs
    '''

    def __init__(self, level):
        '''
        Constructor
        '''
        self.baseSpeed      = 3 # speed constant

        self.state          = EATMAN_IDLE
        self.x              = 0
        self.y              = 0
        self.velocity       = 0 # current speed
        self.direction      = STATIC
        self.idx_frame      = 0
        self.nlifes         = 3

        self.x, self.y = uv_to_xy(level.eatman_xy)

        self.baseSpeed = config.get('Eatman','ibasespeed')
        self.animFreq = config.get('Eatman', 'fanimatefrequency')

        self.load_sprite()

        self.lastAnimTime = time.time()


    def load_sprite(self):
        directions = [DOWN, LEFT, RIGHT, UP] 
        frames = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frames)

        self.frames = {}
        for direc in directions:
            self.frames[direc] = []
            for idx_frame in range(self.nframes):
                filename = os.path.join(SRCDIR,'sprite','eatman-'+direc+'-'+str(frames[idx_frame])+'.gif')
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
                    self.y += self.baseSpeed
                elif self.direction == UP:
                    self.y -= self.baseSpeed
                elif self.direction == LEFT:
                    self.x -= self.baseSpeed
                elif self.direction == RIGHT:
                    self.x += self.baseSpeed
                self.lastAnimTime = time.time()


    def draw(self, DISPLAYSURF):

        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]

        if self.direction == STATIC:
            DISPLAYSURF.blit(self.frames[self.direction], rect)
        else:
            DISPLAYSURF.blit(self.frames[self.direction][self.idx_frame], rect)


class Resource(object):

    def load_tiles(self):

        self.tiles = {}
        files = os.listdir(os.path.join(SRCDIR,'tiles'))
        for filename in files:
            if filename[-3:] == 'gif':
                key = filename[:-4]
                self.tiles[key] = pygame.image.load(os.path.join(SRCDIR,'tiles',filename)).convert()


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


    def load_sounds(self):
        self.sounds = {}
        self.sounds['bean'] = [pygame.mixer.Sound(os.path.join(SRCDIR,'sounds','bean-1.wav')), 
                pygame.mixer.Sound(os.path.join(SRCDIR,'sounds','bean-2.wav'))]
        self.idxBeanSound = 0


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


def check_hit(level, eatman, resource):
    x, y = xy_to_uv((eatman.x, eatman.y))
    if level.data[y][x] == L_BEAN:
        level.data[y][x] = L_EMPTY
        level.map[y][x] = level.get_tile_name(x, y)
        resource.sounds['bean'][resource.idxBeanSound].play()
        resource.idxBeanSound += 1
        if resource.idxBeanSound >=2:
            resource.idxBeanSound = 0


def main():

    pygame.init()

    DISPLAYSURF = pygame.display.set_mode((900, 800))
    pygame.display.set_caption('EatMan')

    clock_fps = pygame.time.Clock()


    level = Level()
    level.load(1)
    level.create_map()

    res = Resource()
    res.load_tiles()
    res.recolor_tiles(level)
    res.load_sounds()

    eatman = Eatman(level)

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False    

    lastMoveTime = time.time()

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
                    # TODO: menu
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
        level.draw(DISPLAYSURF, res)
        eatman.draw(DISPLAYSURF)
        pygame.display.update()

        check_hit(level, eatman, res)

        #clock_fps.tick(FPS)



if __name__ == '__main__':

    main()








