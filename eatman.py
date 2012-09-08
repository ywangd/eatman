#!/usr/bin/env python
import os, sys, time, random, copy
import ConfigParser
import pygame
from pygame.locals import *
import pprint
import genmaze

'''
A Pac-Man clone with improved game mechanics.

ywangd@gmail.com
'''

# TODO
# 1. overal design/structure optimization of the code
# 2. more buffs (electric, wall traspassing, shield)

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        return os.path.dirname(sys.executable)

    return os.path.dirname(__file__)


VERSION                 = 1.0
#SRCDIR                  = os.path.dirname(os.path.abspath(__file__))
SRCDIR                  = module_path() # to make the executable happy

FPS                     = 200
FPS_LOW                 = 30

WINDOW_WIDTH            = 504
WINDOW_HEIGHT           = 600

TILE_WIDTH              = 24
TILE_HEIGHT             = 24

BACKGROUND_COLOR        = (  0,   0,   0)
WALL_FILL_COLOR         = (132,   0, 132)
WALL_BRIGHT_COLOR       = (255, 206, 255)
WALL_SHADOW_COLOR       = (255,   0, 255)
BEAN_FILL_COLOR         = (128,   0, 128)

GAME_STATE_NORMAL       = 0
GAME_STATE_WIN          = 1
GAME_STATE_DYING        = 2
GAME_STATE_DEAD         = 3
GAME_STATE_RESTART      = 4
GAME_STATE_RETURN_TITLE = 5

MAX_LEVEL               = 16
BUTTON_SIZE             = 70
BUTTON_GAP              = 10 
NBUTTON_PER_ROW         = 4
NBUTTON_PER_COL         = 4

STATIC                  = 's'
UP                      = 'u'
DOWN                    = 'd'
LEFT                    = 'l'
RIGHT                   = 'r'

L_TELEPORT              = '$'
L_BLOCK                 = '#' # so no bean will be there, but eatman can move there
L_REAL_BLOCK            = 'X' # no beans and eatman cannot move there
L_WALL                  = '*'
L_GHOST_DOOR            = '='
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
CHOCOLATE               = (210, 105,  30, 255)
GRAY                    = (185, 185, 185, 255)
BURLYWOOD               = (222, 184, 135, 255)

ALL_GHOST_COLORS        = [RED, PINK, CYAN, ORANGE, GRASS, PURPLE, CHOCOLATE, GRAY, BURLYWOOD]

BLUE                    = ( 50,  50, 255, 255)
DARKBLUE                = (  0,   0, 150, 255)
WHITE                   = (248, 248, 248, 255)
BLACK                   = (  0,   0,   0, 255)
YELLOW                  = (255, 255,   0, 255)

BUFF_SLOW               = 'snow'
BUFF_FREEZE             = 'ice'
BUFF_SPEED              = 'boots'
BUFF_BOMB               = 'bomb'
BUFF_ELECTRIC           = 'electric'
BUFF_SHIELD             = 'shield'
BUFF_DAO                = 'dao'
BUFF_1UP                = '1up'
BUFFS_ALL               = [BUFF_SLOW, BUFF_SPEED, BUFF_FREEZE, BUFF_BOMB, 
                           BUFF_SHIELD, BUFF_ELECTRIC, BUFF_DAO, BUFF_1UP]

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

    def load_tiles(self):
        self.tiles = {}
        files = os.listdir(os.path.join(SRCDIR,'tiles'))
        for filename in files:
            if filename[-3:] == 'gif':
                key = filename[:-4]
                self.tiles[key] = pygame.image.load(os.path.join(SRCDIR,'tiles',filename)).convert()

    def load_sounds(self):
        self.sounds = {}
        files = os.listdir(os.path.join(SRCDIR,'sounds'))
        for filename in files:
            if filename[-3:] == 'wav':
                key = filename[:-4]
                self.sounds[key] = pygame.mixer.Sound(os.path.join(SRCDIR,'sounds',filename))


    def load_sprites(self):
        self.fires = {}
        self.ghost_freighten = {}
        self.ghost_recover = {}
        self.glasses = {}
        self.buffs = {}
        self.explosion = {}
        self.fruits = []
        self.lightning = {}

        files = os.listdir(os.path.join(SRCDIR,'sprites'))
        for filename in files:

            if filename == 'lock.gif':
                self.lockimg = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()

            if filename[0:4] == 'fire' and filename[-3:] == 'gif':
                key = filename[:-4]
                self.fires[key] = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()

            if filename[:-6] == 'ghost-freighten' and filename[-3:]=='gif':
                key = filename[:-4]
                img = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()
                img2 = img.copy()

                for ii in range(TILE_WIDTH):
                    for jj in range(TILE_HEIGHT):
                        if img.get_at((ii,jj)) == RED:
                            img.set_at((ii,jj), BLUE)
                self.ghost_freighten[key] = img

                for ii in range(TILE_WIDTH):
                    for jj in range(TILE_HEIGHT):
                        if img2.get_at((ii,jj)) == WHITE:
                            img2.set_at((ii,jj), RED)
                        elif img2.get_at((ii,jj)) == RED:
                            img2.set_at((ii,jj), WHITE)
                self.ghost_recover[key] = img2

            if filename == 'glasses.gif':
                self.glasses['glasses'] = pygame.image.load(
                        os.path.join(SRCDIR,'sprites',filename)).convert()

            if filename[0:-4] in BUFFS_ALL:
                self.buffs[filename[0:-4]] = pygame.image.load(
                        os.path.join(SRCDIR,'sprites',filename)).convert()

            if filename[0:-4] == 'explosion':
                theSurf = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()
                for ii in range(15):
                    self.explosion[ii] = theSurf.subsurface(
                            TILE_WIDTH * (ii%4), TILE_HEIGHT*(ii/4), TILE_WIDTH, TILE_HEIGHT)

            if filename[0:-6] == 'fruit':
                self.fruits.append(
                        pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert())

            if filename[0:-6] == 'lightning':
                key = filename[:-4]
                self.lightning[key] = pygame.image.load(os.path.join(SRCDIR,'sprites',filename)).convert()


    def recolor_tiles(self, level):
        '''
        Re-color the tiles according to the settings in level file.
        '''
        for key in self.tiles:

            if key[0:4] == 'wall':

                for x in range(TILE_WIDTH):
                    for y in range(TILE_HEIGHT):

                        if self.tiles[key].get_at((x,y))==WALL_FILL_COLOR:
                            self.tiles[key].set_at((x,y), level.wallbgcolor)

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
hiscore = 0
hsnames = []
hsvalues = []
score = 0
hilevel = 1
nlifes = 0
score_reward = 0
BASICFONT = None

#################################################################################

class Level(object):

    def __init__(self):
        self.stime = time.time()
        self.wallbgcolor = (0, 0, 0)
        self.beancolor = (255, 255, 255)
        self.wallbrightcolor = (0, 0, 255)
        self.wallshadowcolor = (0, 0, 255)

        self.nbeans = 0
        self.idx_beansound = 0

        self.eatman_params = {}

        self.nghosts = 0
        self.ghost_params = {}
        for ii in range(4):
            self.ghost_params[ii] = {}

        self.uvpos_teleport = []

        self.fruit_lastSpawnTime = time.time()

        # stats of the this level
        self.score_pre = score # previous score for calculate score gained this level
        self.ghost_ate = []
        self.fruit_ate = []
        self.buff_ate = []

    def load(self, iLevel):
        self.iLevel = iLevel

        # set up the available buff pool based on level number
        buff_ub = 2 + (self.iLevel-1) / 2
        if buff_ub > len(BUFFS_ALL):
            buff_ub = len(BUFFS_ALL)
        self.buff_pool = BUFFS_ALL[0:buff_ub]

        # The base parameters for the 4 ghosts
        for ii in range(4):
            fastratio = 0.6 + iLevel*(1.0/30.0)*0.4 # ghost reach max speed at level 30
            if ii==3: # red
                fastratio *= 1.05
            if fastratio > 1.0:
                fastratio = 1.0
            self.ghost_params[ii]['fast'] = fastratio

            if ii==2: # orange
                moltenratio =3 + (iLevel-1)
                if moltenratio >= 50:
                    moltenratio = 50
                self.ghost_params[ii]['molten'] = moltenratio

        filename = os.path.join(SRCDIR, 'levels', str(iLevel)+'.dat') 
        if os.path.exists(filename):
            infile = open(os.path.join(SRCDIR, 'levels', str(iLevel)+'.dat'))
            data = infile.readlines()
        else:
            path_fill_ratio = random.uniform(0.12, 0.16)
            # dimension size, increase by 2 every 4 levels
            nrows = 21 + (iLevel/4)*2
            if nrows > 29:
                nrows = 29
            ncols = 21 + (iLevel/4)*2
            if ncols > 33:
                ncols = 33
            data = genmaze.genmaze(nrows, ncols, path_fill_ratio)

        self.data = []
        for line in data:
            line = line.strip()
            if line != '':
                fields = line.split(' ')

                if fields[0] == 'set': # set variables
                    if fields[1] == 'wallbgcolor':
                        self.wallbgcolor = tuple([int(i) for i in fields[2:]])
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
                        elif attr == 'uvpos_home':
                            fields = val.split(',')
                            self.ghost_params[idx][attr] = [int(fields[0]),int(fields[1])]
                        elif attr == 'tps':
                            self.ghost_params[idx][attr] = val
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

        #self.fruit_interval = config.get('Fruit','finterval') + (self.ncols-21)*5

        # the fruit interval decrease with level number
        self.fruit_interval = config.get('Fruit','finterval') - (self.iLevel-1)*2
        if self.fruit_interval < 40:
            self.fruit_interval = 40
        # set the possible fruit types for the level
        fruit_lb = (self.iLevel-1)/2
        fruit_important = (self.iLevel-1) % 2
        if fruit_lb >= len(resource.fruits)-1:
            fruit_lb = len(resource.fruits)-2
            fruit_important = 0
        self.fruit_pool = [fruit_lb, fruit_lb+1]
        self.fruit_pool.append(self.fruit_pool[fruit_important])

    def analyze_data(self, DISPLAYSURF):

        # Create the surface to display the static objects (e.g. walls)
        self.mazeSurf = DISPLAYSURF.copy()
        # The dynamic objects including beans
        self.dynamicObjects = {}
        self.uvpos_beans = []

        # Analyze the data for tile information
        for v in range(self.nrows):
            for u in range(self.ncols):

                tileRes = self.analyze_tile(u, v) # what is this tile

                # If it is a wall tile
                if tileRes is not None and tileRes[0][0:4] != 'bean':
                    img = resource.tiles[tileRes[0]].copy()
                    # Erase any corner pixels for blocky walls
                    for corner in tileRes[1]:
                        if corner == 'ul':
                            xstart = 0
                            ystart = 0
                        elif corner == 'ur':
                            xstart = 19
                            ystart = 0
                        elif corner == 'll':
                            xstart = 0
                            ystart = 19
                        elif corner == 'lr':
                            xstart = 19
                            ystart = 19
                        for ii in range(5):
                            for jj in range(5):
                                img.set_at((xstart+ii,ystart+jj), self.wallbgcolor)
                    # Draw this wall tile
                    self.mazeSurf.blit(img, uv_to_xy([u, v]))

                # If it is a bean
                elif tileRes is not None and tileRes[0][0:4] == 'bean':
                    img = resource.tiles[tileRes[0]]
                    self.dynamicObjects[uv_to_key([u, v])] = Bean([u, v], img)
                    # get all bean locations
                    self.uvpos_beans.append([u,v])

        # draw other static objects
        # level
        theSurf, theRect = make_text_image('level', BASICFONT, WHITE)
        theRect.center = (WINDOW_WIDTH/2, 12)
        self.mazeSurf.blit(theSurf, theRect)
        
        # score
        theSurf, theRect = make_text_image('score', BASICFONT, WHITE)
        theRect.bottomright = (WINDOW_WIDTH-10, 21)
        self.mazeSurf.blit(theSurf, theRect)

        # high score
        theSurf, theRect = make_text_image('HI score', BASICFONT, WHITE)
        theRect.topleft = (10, 2)
        self.mazeSurf.blit(theSurf, theRect)
        global hiscore, hsnames, hsvalues
        hsnames = []
        hsvalues = []
        try:
            hsfile = open(os.path.join(SRCDIR,'hiscore.txt'))
            for line in hsfile.readlines():
                name, value = line.strip().split(',')
                hsnames.append(name)
                hsvalues.append(int(value))
        except IOError, ValueError:
            pass
        if len(hsnames) < 10:
            for ii in range(10-len(hsnames)):
                hsnames.append('NONAME')
                hsvalues.append(0)
        elif len(hsnames) > 10:
            hsnames = hsnames[0:9]
            hsvalues = hsvalues[0:9]
        hiscore = hsvalues[0]
        # display the highest score
        theSurf, theRect = make_text_image(str(hiscore), BASICFONT, WHITE)
        theRect.topleft = (10, 26)
        self.mazeSurf.blit(theSurf, theRect)

        # The energy bar
        #quarter_width = int(WINDOW_WIDTH/4.0)
        #rect = [quarter_width, WINDOW_HEIGHT - 2*TILE_HEIGHT, quarter_width*2, TILE_HEIGHT]
        #pygame.draw.rect(self.mazeSurf, BLUE, rect)
        #rect[0] += 3
        #rect[1] += 3
        #rect[2] -= 6
        #rect[3] -= 6
        #self.rect_energy = rect
        #pygame.draw.rect(self.mazeSurf, BLACK, rect)
        
        self.buffs = []
        self.energyLevel = range(0, self.nbeans, 65)
        self.energyLevel.append(self.nbeans*2)
        self.idx_energyLevel = 1
        self.energy_decay_time = 2.0
        for ii in range(len(self.energyLevel)-1):
            thebuff = random.choice(self.buff_pool)
            self.buffs.append(thebuff)
            if thebuff == BUFF_1UP: # can only have one 1up buff per level
                self.buff_pool.remove(BUFF_1UP)

        #self.energyLevel = [0]
        #self.energyLevel.append(int(self.nbeans/3))
        #self.energyLevel.append(int(self.nbeans/1.2))
        #self.energyLevel.append(self.nbeans*2)


    def analyze_tile(self, ix, iy):
        '''
        Analyze a character to determine its tile name
        '''
        char = self.data[iy][ix]
        # The chars surround it
        char_u = None if iy==0 else self.data[iy-1][ix]
        char_d = None if iy==self.nrows-1 else self.data[iy+1][ix]
        char_l = None if ix==0 else self.data[iy][ix-1]
        char_r = None if ix==self.ncols-1 else self.data[iy][ix+1]
        # The corner pieces
        char_ul = None if ix==0 or iy==0 else self.data[iy-1][ix-1]
        char_ur = None if ix==self.ncols-1 or iy==0 else self.data[iy-1][ix+1]
        char_ll = None if ix==0 or iy==self.nrows-1 else self.data[iy+1][ix-1]
        char_lr = None if ix==self.ncols-1 or iy==self.nrows-1 else self.data[iy+1][ix+1]

        corner_to_erase = []

        if char == L_EMPTY:
            return None

        elif char == L_WALL: # walls

            if char_u==L_WALL and char_d==L_WALL and char_l==L_WALL and char_r==L_WALL:
                if char_ul == L_WALL: corner_to_erase.append('ul')
                if char_ur == L_WALL: corner_to_erase.append('ur')
                if char_ll == L_WALL: corner_to_erase.append('ll')
                if char_lr == L_WALL: corner_to_erase.append('lr')
                return 'wall-x', corner_to_erase

            if char_u==L_WALL and char_d==L_WALL and char_l==L_WALL:
                if char_ul == L_WALL: corner_to_erase.append('ul')
                if char_ll == L_WALL: corner_to_erase.append('ll')
                return 'wall-t-r', corner_to_erase

            if char_u==L_WALL and char_d==L_WALL and char_r==L_WALL:
                if char_ur == L_WALL: corner_to_erase.append('ur')
                if char_lr == L_WALL: corner_to_erase.append('lr')
                return 'wall-t-l', corner_to_erase

            if char_u==L_WALL and char_l==L_WALL and char_r==L_WALL:
                if char_ul == L_WALL: corner_to_erase.append('ul')
                if char_ur == L_WALL: corner_to_erase.append('ur')
                return 'wall-t-b', corner_to_erase

            if char_d==L_WALL and char_l==L_WALL and char_r==L_WALL:
                if char_ll == L_WALL: corner_to_erase.append('ll')
                if char_lr == L_WALL: corner_to_erase.append('lr')
                return 'wall-t-t', corner_to_erase

            if char_r==L_WALL and char_d==L_WALL:
                if char_lr == L_WALL: corner_to_erase.append('lr')
                return 'wall-corner-ul', corner_to_erase

            if char_r==L_WALL and char_u==L_WALL:
                if char_ur == L_WALL: corner_to_erase.append('ur')
                return 'wall-corner-ll', corner_to_erase

            if char_l==L_WALL and char_d==L_WALL:
                if char_ll == L_WALL: corner_to_erase.append('ll')
                return 'wall-corner-ur', corner_to_erase

            if char_l==L_WALL and char_u==L_WALL:
                if char_ul == L_WALL: corner_to_erase.append('ul')
                return 'wall-corner-lr', corner_to_erase

            if char_l==L_WALL and char_r==L_WALL:
                return 'wall-straight-hori', corner_to_erase

            if char_u==L_WALL and char_d==L_WALL:
                return 'wall-straight-vert', corner_to_erase

            if char_l==L_WALL: 
                return 'wall-end-r', corner_to_erase

            if char_r==L_WALL:
                return 'wall-end-l', corner_to_erase

            if char_u==L_WALL:
                return 'wall-end-b', corner_to_erase

            if char_d==L_WALL:
                return 'wall-end-t', corner_to_erase

            return 'wall-nub', corner_to_erase

        elif char == L_GHOST_DOOR:
            self.uvpos_ghostdoor = [ix, iy]
            return 'ghost-door', corner_to_erase

        elif char == L_EATMAN:
            self.eatman_params['uvpos'] = [ix, iy]
            return None

        elif char in [L_GHOST_0, L_GHOST_1, L_GHOST_2, L_GHOST_3, L_GHOST_4, 
                L_GHOST_5, L_GHOST_6, L_GHOST_7, L_GHOST_8, L_GHOST_9]:
            self.nghosts += 1
            self.ghost_params[int(char)]['uvpos'] = [ix, iy]
            return None

        elif char == L_BEAN_BIG:
            self.nbeans += 1
            return 'bean-big', corner_to_erase

        elif char == L_BEAN:
            self.nbeans += 1
            return 'bean', corner_to_erase

        elif char == L_BLOCK:
            return None

        elif char == L_REAL_BLOCK:
            return None

        elif char == L_TELEPORT:
            self.uvpos_teleport.append([ix, iy])
            return None

        return None


    def draw(self, DISPLAYSURF):

        # draw the maze
        DISPLAYSURF.blit(self.mazeSurf, [0,0])

        # draw the daynamic objects, e.g. beans
        for key in self.dynamicObjects:
            obj = self.dynamicObjects[key]
            DISPLAYSURF.blit(obj.image, uv_to_xy(obj.uvpos))


class FlashingTexts(object):
    
    def __init__(self, text, xypos, duration=1.0):
        self.stime = time.time()
        self.duration = duration
        self.surf, self.rect = make_text_image(text, BASICFONT, GRASS)
        self.rect.topleft = xypos

    def animate(self, DISPLAYSURF):
        if (round(time.time(),1)*10 % 2) == 0:
            DISPLAYSURF.blit(self.surf, self.rect)

    def is_expired(self):
        if time.time()-self.stime > self.duration:
            return True
        else:
            return False

class Explosion(object):

    def __init__(self):
        self.xypos = [0, 0]
        self.active = False
        self.lastAnimTime = time.time()
        self.animFreq = config.get('Buff','fexplosion_animatefrequency')
        self.idx_frame = 0
        self.frame_sequence = range(14,-1,-1) + [0]

    def start(self, xypos):
        self.xypos = copy.copy(xypos)
        self.active = True
        self.lastAnimTime = time.time()
        resource.sounds['explosion'].play()

    def animate(self, DISPLAYSURF):
        if not self.active:
            return

        id = self.frame_sequence[self.idx_frame]
        DISPLAYSURF.blit(resource.explosion[id], self.xypos)
        if time.time()-self.lastAnimTime > self.animFreq:
            self.idx_frame += 1
            self.lastAnimTime = time.time()
            if self.idx_frame >= len(self.frame_sequence):
                self.idx_frame = 0
                self.active = False


class Fire(object):

    def __init__(self, uvpos):

        self.uvpos = uvpos
        self.xypos = uv_to_xy(uvpos)
        self.stime = time.time()

        self.lastAnimTime = time.time()
        self.duration = config.get('Fire','fduration') # last for how many seconds
        self.animFreq = config.get('Fire','fanimatefrequency')
        self.idx_frame = 0
        self.frame_sequence = [1,2,3,4,5,6,7,8,1]

    def animate(self, DISPLAYSURF):
        id = self.frame_sequence[self.idx_frame]
        DISPLAYSURF.blit(resource.fires['fire-'+str(id)], self.xypos)
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


class Fruit(object):

    MOTION_IDLE = 1
    MOTION_ANIMATE = 2

    lastSpawnTime = time.time()
    
    def __init__(self, level):
        self.animFreq = config.get('Fruit','fanimatefrequency')
        self.speed = config.get('Fruit', 'ispeed')
        self.stime = time.time()
        self.duration = config.get('Fruit', 'fduration')
        fruitid = random.choice(level.fruit_pool)
        self.surf = resource.fruits[fruitid]
        self.score = 300 + fruitid*100
        self.xypos = uv_to_xy(random.choice(level.uvpos_teleport))
        self.pathway = RIGHT if self.xypos[0] <= TILE_WIDTH else LEFT
        self.movedFrom = None
        self.direction = self.pathway
        self.motion = Fruit.MOTION_ANIMATE
        self.idx_frame = 0
        self.y_adjust = [0, 1, 2, 3, 4, 3, 2, 1, 0]
        self.nframes = len(self.y_adjust)
        self.lastAnimTime = self.stime

    def draw(self, DISPLAYSURF):
        # we need to adjust y position for bumping effects
        if time.time()-self.stime > self.duration - 1.5:
            if self.idx_frame % 2 == 0:
                DISPLAYSURF.blit(self.surf, (self.xypos[0], self.xypos[1]+self.y_adjust[self.idx_frame]))
        else:
            DISPLAYSURF.blit(self.surf, (self.xypos[0], self.xypos[1]+self.y_adjust[self.idx_frame]))

    def make_move(self, level):
        if self.motion == Fruit.MOTION_ANIMATE and time.time()-self.lastAnimTime>self.animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.motion = Fruit.MOTION_IDLE
                self.movedFrom = get_opposite_direction(self.direction)
                resource.sounds['fruitbounce'].play()
            else:
                if self.direction == DOWN:
                    self.xypos[1] += self.speed
                elif self.direction == UP:
                    self.xypos[1] -= self.speed
                elif self.direction == LEFT:
                    self.xypos[0] -= self.speed
                elif self.direction == RIGHT:
                    self.xypos[0] += self.speed
                self.lastAnimTime = time.time()

        if self.motion == Fruit.MOTION_IDLE:
            if self.pathway is not None and len(self.pathway) > 0:
                self.follow_pathway()
                return
            self.pathway = randpath(level, self)
            self.follow_pathway()

    def follow_pathway(self):
        if len(self.pathway) > 0:
            moveto = self.pathway[0]
            self.pathway = self.pathway[1:]
            self.motion = Ghost.MOTION_ANIMATE
            self.direction = moveto
        else:
            self.motion = Ghost.MOTION_IDLE
            self.direction = STATIC

    def is_expired(self):
        if time.time()-self.stime > self.duration:
            return True
        else:
            return False


class Buff(object):

    INSIDE_MAP = 0
    OUTSIDE_MAP = 1

    def __init__(self):
        self.uvpos = [-1, -1]
        self.xypos = [0, 0]
        self.stime = time.time()
        self.duration = config.get('Buff','fduration')
        self.active = False

    def start(self, level, type=None):
        self.active = True
        self.state = Buff.INSIDE_MAP
        self.uvpos = random.choice(level.uvpos_beans)
        self.xypos = uv_to_xy(self.uvpos)
        self.duration = config.get('Buff','fduration')
        if type is None:
            self.type = level.buffs[level.idx_energyLevel-1]
            level.idx_energyLevel += 1
        else:
            self.type = type
        self.surf = resource.buffs[self.type]
        self.stime = time.time()

    def apply(self, eatman, ghosts, fires, explosion, electric):
        if self.type == BUFF_SLOW:
            for ghost in ghosts:
                ghost.add_freq_modifier(
                        config.get('Buff','fslow_rate'), 
                        config.get('Buff','fslow_duration')) 
            self.duration = config.get('Buff','fslow_duration')
        elif self.type == BUFF_FREEZE:
            for ghost in ghosts: # slow 99999.9 times
                ghost.add_freq_modifier(
                        99999.9, config.get('Buff','ffreeze_duration')) 
            self.duration = config.get('Buff','ffreeze_duration')
        elif self.type == BUFF_BOMB: # randomly blow up a ghost
            ghost_to_die = []
            for ghost in ghosts:
                if ghost.mode != Ghost.MODE_DYING and ghost.mode != Ghost.MODE_DEAD:
                    ghost_to_die.append(ghost)
            if len(ghost_to_die) > 0:
                ghost_to_die = random.choice(ghost_to_die)
                ghost_to_die.mode = Ghost.MODE_DYING
                ghost_to_die.add_freq_modifier(
                        99999.9, len(explosion.frame_sequence)*explosion.animFreq, 
                        exclude_modes=[])
                explosion.start(ghost_to_die.xypos)
            self.duration = 0.0
            self.active = False
        elif self.type == BUFF_SPEED:
            eatman.add_freq_modifier(
                    config.get('Buff','fspeed_rate'), 
                    config.get('Buff','fspeed_duration')) 
            self.duration = config.get('Buff','fspeed_duration')

        elif self.type == BUFF_ELECTRIC:
            electric.start(self.xypos)
            self.duration = 0.0
            self.active = False

        elif self.type == BUFF_SHIELD:
            eatman.mode = Eatman.MODE_UNDYING
            self.duration = config.get('Buff','fshield_duration')

        elif self.type == BUFF_DAO:
            eatman.mode = Eatman.MODE_DAO
            self.duration = config.get('Buff','fdao_duration')

        elif self.type == BUFF_1UP:
            global nlifes
            nlifes += 1
            resource.sounds['extralife'].play()
            self.duration = 0.0
            self.active = False

        self.state = Buff.OUTSIDE_MAP
        self.stime = time.time()
        self.uvpos = [-1, -1]
        self.xypos = [WINDOW_WIDTH-TILE_WIDTH-10, WINDOW_HEIGHT-1*TILE_HEIGHT-18]


    def draw(self, DISPLAYSURF, eatman):
        if not self.active:
            return

        if time.time()-self.stime > self.duration - 1.5:
            if round(time.time()*10) % 2 == 0:
                DISPLAYSURF.blit(self.surf, self.xypos)
        else:
            DISPLAYSURF.blit(self.surf, self.xypos)

        if self.state == Buff.INSIDE_MAP and round(time.time()*10) % 5 == 0:
            pygame.draw.rect(DISPLAYSURF, WHITE, 
                    self.xypos + [TILE_WIDTH, TILE_HEIGHT], 1)

        if self.is_expired():
            self.stop(eatman)

    def is_expired(self):
        if time.time()-self.stime > self.duration:
            return True
        else:
            return False

    def stop(self, eatman):
        self.active = False
        eatman.mode = Eatman.MODE_NORMAL


class Electric(object):

    def __init__(self):
        self.stime = time.time()
        self.lastAnimTime = time.time()
        self.duration = config.get('Buff','felectric_duration')
        self.animFreq = config.get('Buff','felectric_animatefrequency')
        self.idx_frame = 0
        self.frame_sequence = [1,2,3,1]
        self.active = False

    def start(self, xypos):
        self.xypos = xypos
        self.uvpos = xy_to_uv(xypos)
        self.active = True
        self.stime = time.time()

    def animate(self, DISPLAYSURF):
        if not self.active:
            return

        id = self.frame_sequence[self.idx_frame]
        DISPLAYSURF.blit(resource.lightning['lightning-'+str(id)], self.xypos)
        if time.time()-self.lastAnimTime > self.animFreq:
            self.idx_frame += 1
            self.lastAnimTime = time.time()
            if self.idx_frame >= len(self.frame_sequence):
                self.idx_frame = 0

        if self.is_expired():
            self.active = False

    def is_expired(self):
        if time.time()-self.stime > self.duration:
            return True
        else:
            return False

class Ghost(object):

    # The pupil locations
    PUPIL_L = (5, 8)
    PUPIL_R = (8, 7)
    PUPIL_U = (6, 5)
    PUPIL_D = (7, 10)

    # Motion
    MOTION_IDLE      = 1
    MOTION_ANIMATE   = 2

    # mode
    MODE_SCATTER   = 0
    MODE_CHASE     = 1
    MODE_DEAD      = 2
    MODE_DYING     = 3
    MODE_FREIGHTEN = 4
    MODE_EXPLODING = 5

    # Target picking strategy
    TPS_WHIMSICAL = 0
    TPS_AMBUSHER  = 1
    TPS_IGNORANCE = 2
    TPS_PURSUER   = 3
    TPS_ALL = [TPS_WHIMSICAL, TPS_AMBUSHER, TPS_IGNORANCE, TPS_PURSUER]

    # The pursuer is special since whimsical will use pursuer and eatman's
    # position to choose its target
    pursuer = None


    def __init__(self, idx, level, eatman):

        self.id = idx
        self.motion = Ghost.MOTION_IDLE
        self.animFreq = config.get('Ghost','fanimatefrequency')
        self.freq_modifier = {}
        self.speed = config.get('Ghost','ispeed')
        self.pathway = ''

        self.mode = Ghost.MODE_SCATTER
        self.oldMode = self.mode

        self.nalters = 0 # how many mode alternation has happened
        self.lastMaTime = time.time() # last mode alternation time

        self.mode_duration_base = {}

        self.mode_duration_base[Ghost.MODE_SCATTER] = 6 - level.iLevel*0.5
        if self.mode_duration_base[Ghost.MODE_SCATTER] < 0:
            self.mode_duration_base[Ghost.MODE_SCATTER] = 0.02

        self.mode_duration_base[Ghost.MODE_CHASE] = 15 + level.iLevel
        self.mode_duration = self.generate_mode_duration()

        self.lastDeadTime = time.time()
        self.dead_duration = 5.0

        self.xypos = uv_to_xy(level.ghost_params[idx]['uvpos'])
        self.uvpos_target = [0, 0]
        # The ghost reset position is always the first ghost's starting position
        self.uvpos_dyingto = [level.uvpos_ghostdoor[0], level.uvpos_ghostdoor[1]+1]

        self.pupil_color = BLACK
        self.pupil_pos = random.choice(
                        [Ghost.PUPIL_L, Ghost.PUPIL_R, Ghost.PUPIL_U, Ghost.PUPIL_D])
        self.direction = STATIC
        self.movedFrom = None
        self.idx_frame = 0
        self.lastAnimTime = time.time()

        self.lastIndoorTime = time.time()

        # Default settings for different IDs
        if idx == 0:
            self.color = CYAN
            self.uvpos_home = [level.ncols-1, level.nrows+1]
            self.tps = Ghost.TPS_WHIMSICAL
            self.indoor_duration = 5 - level.iLevel*0.5
            if self.indoor_duration < 0:
                self.indoor_duration = 0
        elif idx == 1:
            self.color = PINK
            self.uvpos_home = [2, -2]
            self.tps = Ghost.TPS_AMBUSHER
            self.indoor_duration = 0
        elif idx == 2:
            self.color = ORANGE
            self.uvpos_home = [0, level.nrows+1]
            self.tps = Ghost.TPS_IGNORANCE
            self.indoor_duration = 10 - level.iLevel*0.5
            if self.indoor_duration < 0:
                self.indoor_duration = 0
        elif idx == 3:
            self.color = RED
            self.uvpos_home = [level.ncols-3, -2]
            self.tps = Ghost.TPS_PURSUER
            self.indoor_duration = 0
        else:
            self.color = random.choice(ALL_GHOST_COLORS)
            self.uvpos_home = [level.ncols-3, -2]
            self.tps = random.choice(Ghost.TPS_ALL)
            self.indoor_duration = random.randint(0,10) - level.iLevel*0.5
            if self.indoor_duration < 0:
                self.indoor_duration = 0

        # The pursuer is speical
        if self.tps == Ghost.TPS_PURSUER and Ghost.pursuer is None:
            Ghost.pursuer = self


        # Overwrite with level file settings
        if level.ghost_params[idx].has_key('color'):
            self.color = level.ghost_params[idx]['color']

        if level.ghost_params[idx].has_key('uvpos_home'):
            self.uvpos_home = level.ghost_params[idx]['uvpos_home']

        if level.ghost_params[idx].has_key('tps'):
            self.tps = vars(Ghost)[level.ghost_params[idx]['tps']]

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
            eatman.add_freq_modifier(level.ghost_params[idx]['chilling'], -1)

        # Load the images
        self.load_sprites()

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
            # Add this frame to the list
            self.frames.append(img)

    def generate_mode_duration(self):

        if self.mode == Ghost.MODE_SCATTER:
            adjustment = -self.nalters
        elif self.mode == Ghost.MODE_CHASE:
            if self.nalters >3:
                adjustment = 99999
            else:
                adjustment = self.nalters*2

        mode_duration = self.mode_duration_base[self.mode] + adjustment
        if mode_duration < 0:
            mode_duration = 0.02

        return mode_duration

    def move_outdoor(self, level):
        if time.time() - self.lastIndoorTime < self.indoor_duration:
            return False

        # get out of the door
        uvpos = xy_to_uv(self.xypos)
        if uvpos[1] == level.uvpos_ghostdoor[1]+1 \
                and uvpos[0] >= level.uvpos_ghostdoor[0]-1 \
                and uvpos[0] <= level.uvpos_ghostdoor[0]+1:
            if uvpos[0] == level.uvpos_ghostdoor[0]-1:
                self.pathway = 'ruu'
            elif uvpos[0] == level.uvpos_ghostdoor[0]:
                self.pathway = 'uu'
            elif uvpos[0] == level.uvpos_ghostdoor[0]+1:
                self.pathway = 'luu'
            return True

        return False


    def alter_mode(self):

        # We only need alter the mode when the ghost is in scatter or chase mode
        if (self.mode == Ghost.MODE_SCATTER or self.mode == Ghost.MODE_CHASE) \
                and time.time()-self.lastMaTime > self.mode_duration:

            if self.mode == Ghost.MODE_SCATTER:
                self.mode = Ghost.MODE_CHASE
            elif self.mode == Ghost.MODE_CHASE:
                self.mode = Ghost.MODE_SCATTER

            self.mode_duration = self.generate_mode_duration()
            self.lastMaTime = time.time()
            # reverse the direction when mode alternation happens
            self.pathway = get_opposite_direction(self.direction)
            self.nalters += 1

            return True

        return False

    # all modifier will be used in multiplications
    def add_freq_modifier(self, value, duration, exclude_modes=None):
        if exclude_modes is None:
            exclude_modes = [Ghost.MODE_DYING, Ghost.MODE_DEAD]
        if self.mode not in exclude_modes:
            stime = time.time()
            name = str(random.random()) + str(stime)
            self.freq_modifier[name] = (value, stime, duration)
            return name
        return None


    def draw(self, DISPLAYSURF, eatman):

        # No drawing is necessary when the ghost is dead
        if self.mode == Ghost.MODE_DEAD:
            return

        # if ghost is dying to reset position, the image is a pair of glasses
        if self.mode == Ghost.MODE_DYING: 
            img = resource.glasses['glasses']

        # if ghost is freightened, they are in blue color
        elif self.mode == Ghost.MODE_FREIGHTEN: 
            idx_frame = self.idx_frame % len(resource.ghost_freighten) + 1
            img = resource.ghost_freighten['ghost-freighten-'+str(idx_frame)]
            # Flash the ghost when the freighten timer has 1.5 seconds left
            if time.time()-eatman.lastSlayerTime > config.get('Eatman','fslayerduration')-1.5:
                if idx_frame % 2 == 0:
                    img = resource.ghost_recover['ghost-freighten-'+str(idx_frame)]

        # All the other modes, scatter, chase
        else:
            img = self.frames[self.idx_frame].copy()
            # set the eye ball position
            if self.direction == LEFT:
                self.pupil_pos = Ghost.PUPIL_L
            elif self.direction == RIGHT:
                self.pupil_pos = Ghost.PUPIL_R
            elif self.direction == UP:
                self.pupil_pos = Ghost.PUPIL_U
            elif self.direction == DOWN:
                self.pupil_pos = Ghost.PUPIL_D
            else:
                self.pupil_pos = random.choice(
                        [Ghost.PUPIL_L, Ghost.PUPIL_R, Ghost.PUPIL_U, Ghost.PUPIL_D])
            # draw eye balls
            for y in range(self.pupil_pos[1], self.pupil_pos[1]+3):
                for x in range(self.pupil_pos[0], self.pupil_pos[0]+2):
                    img.set_at((x,y), self.pupil_color)
                    img.set_at((x+9,y), self.pupil_color)

        # Draw the actual image
        DISPLAYSURF.blit(img, self.xypos)


    def make_move(self, level, eatman, fires):

        # If the ghost is dead, we may not need any moves
        if self.mode == Ghost.MODE_DEAD:
            # if the dead timer expires, we let the ghost return to scatter mode and reset timers
            if time.time()-self.lastDeadTime > self.dead_duration:
                self.mode = Ghost.MODE_SCATTER
                self.mode_duration = self.generate_mode_duration()
                self.lastMaTime = time.time() 
                # the ghost is respawned and ready to make moves now
            else:
                return # the ghost is still dead and no move is needed

        # If the ghost is in freightened mode
        if self.mode == Ghost.MODE_FREIGHTEN:
            # check if the mode expires
            if time.time()-eatman.lastSlayerTime > config.get('Eatman','fslayerduration'):
                self.mode = self.oldMode # restore the old mode before the freightened mode
                self.lastMaTime += time.time() - eatman.lastSlayerTime # re-calculate timers
                # now ready to make moves

        # Calculate its animation frequency
        animFreq = self.animFreq

        # Make ghost move faster when dying, no other frequency factor should be used
        if self.mode == Ghost.MODE_DYING: 
            animFreq *= 0.25

        else:
            # Make ghost move slower when its freightened
            if self.mode == Ghost.MODE_FREIGHTEN:
                animFreq *= 3.0

        # Modify the animate frequency through the modifiers
        for key in self.freq_modifier.keys():
            value, stime, duration = self.freq_modifier[key]
            if duration < 0 or time.time()-stime < duration:
                animFreq *= value
            else:
                del self.freq_modifier[key]


        # If it is in middle of an animation and its time to refresh a new frame 
        # keep doing it till the cycle is done.
        if self.motion == Ghost.MOTION_ANIMATE and time.time()-self.lastAnimTime>animFreq:
            self.idx_frame += 1
            # if we are at the last frame of the cycle, we need to reset the frame
            # and make the ghost idle and ready for next move
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.motion = Ghost.MOTION_IDLE
                self.movedFrom = get_opposite_direction(self.direction)
                # drop a fire only when a motion cycle is completed
                if self.mode == Ghost.MODE_SCATTER or self.mode == Ghost.MODE_CHASE:
                    if self.moltenPercent>0 and len(fires)<config.get('Fire','imaxfire') \
                            and random.randint(1,100)<self.moltenPercent:
                        fires.append(Fire(xy_to_uv(self.xypos)))
            else: # animate this frame
                if self.direction == DOWN:
                    self.xypos[1] += self.speed
                elif self.direction == UP:
                    self.xypos[1] -= self.speed
                elif self.direction == LEFT:
                    self.xypos[0] -= self.speed
                elif self.direction == RIGHT:
                    self.xypos[0] += self.speed
                self.lastAnimTime = time.time()

        # If it is not animating, we need to figure out where to go for the next animation cycle
        # NOTE: this must be a separate if, not an elif
        if self.motion == Ghost.MOTION_IDLE:

            # simply follow the pathway if it is not empty
            if self.pathway is not None and len(self.pathway) > 0:
                self.follow_pathway()
                return

            # if the ghost is dying to reset point
            if self.mode == Ghost.MODE_DYING:
                # if the ghost has reached the reset point, we make it dead
                if self.uvpos_dyingto == xy_to_uv(self.xypos):
                    self.mode = Ghost.MODE_DEAD
                    self.pathway = ''
                    self.freq_modifier = {} # clear all freq modifier
                    self.lastDeadTime = time.time()
                else:
                    self.pathway = simplepath(level, self, self.uvpos_dyingto)
                    # now we can follow the path

            # if the ghost is freightened, we make random path
            elif self.mode == Ghost.MODE_FREIGHTEN: 
                self.pathway = randpath(level, self)
                # now we can follow the path

            else:  # normal state behaviour

                # Try alter the mode only in idle motion and scatter or chase mode
                self.alter_mode() # this may give a new path 
                # Try move out of the door only in idle motion and scatter or chase mode
                self.move_outdoor(level) # this may give a new path too

                if self.pathway is not None and len(self.pathway) > 0:
                    self.follow_pathway()
                    return

                # In scatter mode, the ghost seek to its home position
                if self.mode == Ghost.MODE_SCATTER:
                    euvpos = self.uvpos_home

                elif self.mode == Ghost.MODE_CHASE:
                    # generate a path based on the ghost's target picking strategy
                    # whimsical tries to help the pursuer
                    if self.tps == Ghost.TPS_WHIMSICAL:
                        e_uvpos = xy_to_uv(eatman.xypos)
                        g_uvpos = xy_to_uv(Ghost.pursuer.xypos)
                        euvpos = [g_uvpos[0] + 2*(e_uvpos[0] - g_uvpos[0]), 
                                g_uvpos[1] + 2*(e_uvpos[1] - g_uvpos[1])]

                    # Ambuser tries to get ahead of the eatman
                    elif self.tps == Ghost.TPS_AMBUSHER:
                        euvpos = xy_to_uv(eatman.xypos)
                        if eatman.direction == UP:
                            euvpos[1] -= 4
                        elif eatman.direction == DOWN:
                            euvpos[1] += 4
                        elif eatman.direction == LEFT:
                            euvpos[0] -= 4
                        elif eatman.direction == RIGHT:
                            euvpos[0] += 4

                    # ignorance will chase if too far but leave if too close
                    elif self.tps == Ghost.TPS_IGNORANCE:
                        e_uvpos = xy_to_uv(eatman.xypos)
                        g_uvpos = xy_to_uv(self.xypos)
                        if calc_distsq(g_uvpos, e_uvpos) > 64:
                            euvpos = e_uvpos
                        else:
                            euvpos = self.uvpos_home

                    elif self.tps == Ghost.TPS_PURSUER:
                        euvpos = xy_to_uv(eatman.xypos)

                # Generate the pathway
                self.pathway = simplepath(level, self, euvpos)

            # now follow the pathway
            self.follow_pathway()


    def follow_pathway(self):
        if len(self.pathway) > 0:
            moveto = self.pathway[0]
            self.pathway = self.pathway[1:]
            self.motion = Ghost.MOTION_ANIMATE
            self.direction = moveto
        else:
            self.motion = Ghost.MOTION_IDLE
            self.direction = STATIC



class Eatman(object):
    '''
    The Eatman class for managing the Player.
    '''

    # Motion
    MOTION_IDLE         = 1
    MOTION_ANIMATE      = 2

    MODE_NORMAL         = 0
    MODE_UNDYING        = 1
    MODE_DAO            = 2
    MODE_DAO_PASSING    = 3

    def __init__(self, level):

        self.motion          = Eatman.MOTION_IDLE
        self.direction      = STATIC

        self.mode           = Eatman.MODE_NORMAL

        self.xypos = uv_to_xy(level.eatman_params['uvpos'])

        self.animFreq = config.get('Eatman', 'fanimatefrequency')
        self.speed = config.get('Eatman','ispeed')

        self.freq_modifier = {}

        self.load_sprites()
        self.idx_frame      = 0
        self.lastAnimTime = time.time()

        self.lastSlayerTime = time.time()

        self.energy = 0
        self.lastEatTime = time.time()


    def load_sprites(self):
        directions = [DOWN, LEFT, RIGHT, UP] 
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        # frames for moving all directions
        self.frames = {}
        for direc in directions:
            self.frames[direc] = []
            for idx_frame in range(self.nframes):
                filename = os.path.join(
                        SRCDIR,'sprites','eatman-'+direc+'-'+str(frame_sequence[idx_frame])+'.gif')
                self.frames[direc].append(pygame.image.load(filename).convert())
        # the static one
        self.frames[STATIC] = pygame.image.load(os.path.join(SRCDIR,'sprites','eatman.gif')).convert()

        # load the dead animation
        self.frames_dead = []
        self.frames_dead.append(
                pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-u-5.gif')).convert())
        for idx in range(1,10):
            self.frames_dead.append(
                    pygame.image.load(
                        os.path.join(SRCDIR,'sprites','eatman-dead-'+str(idx)+'.gif')).convert())
        self.frames_dead.append(self.frames_dead[0].copy())
        self.frames_dead[-1].fill(BACKGROUND_COLOR)


    # all modifier will be used in multiplications
    def add_freq_modifier(self, value, duration):
        stime = time.time()
        name = str(random.random()) + str(stime)
        self.freq_modifier[name] = (value, stime, duration)
        return name


    def make_move(self, buff):

        # modify the animation frequency by any buff/debuff
        animFreq = self.animFreq
        for key in self.freq_modifier.keys():
            value, stime, duration = self.freq_modifier[key]
            if duration < 0 or time.time()-stime < duration:
                animFreq *= value
            else:
                del self.freq_modifier[key]

        # Only animate the player if it is in animate state and with proper frequency
        if self.motion == Eatman.MOTION_ANIMATE and time.time()-self.lastAnimTime>animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.motion = Eatman.MOTION_IDLE
                if self.mode == Eatman.MODE_DAO_PASSING:
                    if buff.active:
                        self.mode = Eatman.MODE_DAO
                    else:
                        self.mode = Eatman.MODE_NORMAL
            else:
                if self.direction == DOWN:
                    self.xypos[1] += self.speed
                elif self.direction == UP:
                    self.xypos[1] -= self.speed
                elif self.direction == LEFT:
                    self.xypos[0] -= self.speed
                elif self.direction == RIGHT:
                    self.xypos[0] += self.speed
                self.lastAnimTime = time.time()


    def draw(self, DISPLAYSURF):

        if self.direction == STATIC:
            DISPLAYSURF.blit(self.frames[self.direction], self.xypos)
        else:
            DISPLAYSURF.blit(self.frames[self.direction][self.idx_frame], self.xypos)

    def animate_dead(self, DISPLAYSURF):

        # Animate it
        if time.time()-self.lastAnimTime>self.animFreq*3.0:
            self.idx_frame += 1
            self.lastAnimTime = time.time()
            if self.idx_frame >= len(self.frames_dead):
                self.idx_frame = 0
                return GAME_STATE_DEAD

        # drawing
        DISPLAYSURF.blit(self.frames_dead[self.idx_frame], self.xypos)

        return GAME_STATE_DYING



class Bean(object):
    def __init__(self, uvpos, image):
        self.uvpos = uvpos
        self.image = image


def randpath(level, ghost):
    moveto = [UP, LEFT, DOWN, RIGHT]
    if ghost.movedFrom == UP or (not is_valid_position(level, ghost, voffset=-1)):
        moveto.remove(UP)
    if ghost.movedFrom == DOWN or (not is_valid_position(level, ghost, voffset=1)):
        moveto.remove(DOWN)
    if ghost.movedFrom == LEFT or (not is_valid_position(level, ghost, uoffset=-1)):
        moveto.remove(LEFT)
    if ghost.movedFrom == RIGHT or (not is_valid_position(level, ghost, uoffset=1)):
        moveto.remove(RIGHT)

    if len(moveto) == 0:
        return ghost.movedFrom

    return random.choice(moveto)


def simplepath(level, ghost, euvpos):
    su, sv = xy_to_uv(ghost.xypos)
    eu, ev = euvpos
    
    moveto = [UP, LEFT, DOWN, RIGHT]
    if ghost.movedFrom == UP or (not is_valid_position(level, ghost, voffset=-1)):
        moveto.remove(UP)
    if ghost.movedFrom == DOWN or (not is_valid_position(level, ghost, voffset=1)):
        moveto.remove(DOWN)
    if ghost.movedFrom == LEFT or (not is_valid_position(level, ghost, uoffset=-1)):
        moveto.remove(LEFT)
    if ghost.movedFrom == RIGHT or (not is_valid_position(level, ghost, uoffset=1)):
        moveto.remove(RIGHT)

    if len(moveto) == 0:
        return ghost.movedFrom

    mindist = 1e20 # Arbitrary high cost
    for mt in moveto:
        if mt == UP:
            dist = (su - eu)**2 + (sv-1 - ev)**2
        elif mt == LEFT:
            dist = (su-1 - eu)**2 + (sv - ev)**2
        elif mt == DOWN:
            dist = (su - eu)**2 + (sv+1 - ev)**2
        elif mt == RIGHT:
            dist = (su+1 - eu)**2 + (sv - ev)**2

        if mindist > dist:
            mindist = dist
            choice = mt

    return choice


def calc_distsq(spos, epos):
    return (spos[0]-epos[0])**2 + (spos[1]-epos[1])**2


def uv_to_key(uvpos):
    '''
    Create a dictionary key using the u, v grid cell coordinates
    '''
    return str(uvpos[0]) + ',' + str(uvpos[1])


# x, y is column, row
def xy_to_uv(xypos):
    '''
    Convert the screen pixel coordinates to the board grid coordinates.
    The results are rounded to the nearest integers.
    '''
    return [int(round((xypos[0]-config.get('Game','ixmargin'))*1.0/TILE_WIDTH)),
            int(round((xypos[1]-config.get('Game','iymargin'))*1.0/TILE_HEIGHT))]

def uv_to_xy(uvpos):
    '''
    Convert the board grid coordinates to screen pixel coordinates
    '''
    return [config.get('Game','ixmargin')+uvpos[0]*TILE_WIDTH,
            config.get('Game','iymargin')+uvpos[1]*TILE_HEIGHT]

def get_opposite_direction(direction):
    if direction == UP:
        return DOWN
    if direction == DOWN:
        return UP
    if direction == LEFT:
        return RIGHT
    if direction == RIGHT:
        return LEFT
    if direction == STATIC:
        return None



def is_valid_position(level, entity, uoffset=0, voffset=0):

    u, v = xy_to_uv(entity.xypos)
    u += uoffset
    v += voffset

    if u >= level.ncols or v >=level.nrows or u < 0 or v < 0:
        return False

    blocks = [L_WALL, L_GHOST_DOOR]
    if isinstance(entity, Ghost) and entity.mode==Ghost.MODE_DYING:
        blocks.remove(L_GHOST_DOOR)

    if level.data[v][u] not in blocks:
        return True
    else:
        if isinstance(entity, Eatman) and entity.mode==Eatman.MODE_DAO:
            if level.data[v][u] == L_WALL \
                    and u>0 and v>0 and u<level.nrows-1 and v<level.ncols-1 \
                    and level.data[v+voffset][u+uoffset] not in \
                    blocks+[L_REAL_BLOCK,L_GHOST_0,L_GHOST_1,L_GHOST_2]:
                return True
        return False


def check_hit(level, eatman, ghosts, fires, fruits, ftexts, explosion, buff, electric):

    global score, score_reward, nlifes

    u, v = xy_to_uv(eatman.xypos)

    if level.data[v][u] == L_WALL:
        eatman.mode = Eatman.MODE_DAO_PASSING

    # Going through the ends of the tunnels
    if u == 0: 
        eatman.xypos = [(level.ncols-2)*TILE_WIDTH+eatman.xypos[0], eatman.xypos[1]]
        u = level.ncols - 2
    elif u == level.ncols-1:
        eatman.xypos = [eatman.xypos[0]-(level.ncols-2)*TILE_WIDTH, eatman.xypos[1]]
        u, v = xy_to_uv(eatman.xypos) 
        u = 1

    # hit a ghost?
    neats = 0
    isJustEat = False
    for ghost in ghosts:
        gu, gv = xy_to_uv(ghost.xypos)
        # Going through the ends of the tunnels
        if gu == 0:
            ghost.xypos = [(level.ncols-2)*TILE_WIDTH+ghost.xypos[0], ghost.xypos[1]]
            gu = level.ncols - 2
        elif gu == level.ncols-1:
            ghost.xypos = [ghost.xypos[0]-(level.ncols-2)*TILE_WIDTH, ghost.xypos[1]]
            gu = 1
        # check the hit of eatman and ghost
        if [u, v] == [gu, gv]:
            if ghost.mode == Ghost.MODE_FREIGHTEN:
                # eat a ghost
                ghost.mode = Ghost.MODE_DYING
                ghost.freq_modifier = {}
                score += 100
                neats += 1
                level.ghost_ate.append(ghost.id)
                isJustEat = True
                eatman.lastEatTime = time.time()
                resource.sounds['eatghost'].play()
            elif ghost.mode == Ghost.MODE_DYING or ghost.mode == Ghost.MODE_DEAD:
                neats += 1
            elif eatman.mode == Eatman.MODE_UNDYING: # shield 
                pass
            else:
                # killed by a ghost
                eatman.idx_frame = 0
                return GAME_STATE_DYING
        elif electric.active and ghost.mode != Ghost.MODE_DYING and electric.uvpos == [gu, gv]:
                ghost.mode = Ghost.MODE_DYING
                ghost.freq_modifier = {}
                score += 100
                neats += 1
                level.ghost_ate.append(ghost.id)
                isJustEat = True
                eatman.lastEatTime = time.time()
        else:
            if ghost.mode == Ghost.MODE_DYING or ghost.mode == Ghost.MODE_DEAD:
                neats += 1
    # bonus score for eating all ghosts
    # isJustEat is used to prevent the score being awarded multiple times when
    # all ghosts are dead. It ensure the awards only happens when the EatMan just
    # eat the last alive ghost
    if neats == len(ghosts) and isJustEat:
        score += 1000
        ftexts.append(FlashingTexts('1000', eatman.xypos))

    # hit a fire?
    for fire in fires:
        if fire.uvpos == [u, v] and eatman.mode != Eatman.MODE_UNDYING:
            eatman.idx_frame = 0
            return GAME_STATE_DYING

    # hit a fruit?
    for id in range(len(fruits)-1,-1,-1):
        if [u, v] == xy_to_uv(fruits[id].xypos):
            resource.sounds['eatfruit'].play()
            score += fruits[id].score
            level.fruit_ate.append(fruits[id].surf)
            ftexts.append(FlashingTexts(str(fruits[id].score), fruits[id].xypos))
            del fruits[id]

    # Check if a bean is hit
    if level.data[v][u] == L_BEAN:
        level.data[v][u] = L_EMPTY
        del level.dynamicObjects[uv_to_key([u, v])]
        level.nbeans -= 1
        score += 1
        eatman.energy += 1
        eatman.lastEatTime = time.time()
        resource.sounds['bean-'+str(level.idx_beansound)].play()
        level.idx_beansound += 1
        if level.idx_beansound >=2:
            level.idx_beansound = 0
        # check if energy is full
        if eatman.energy > level.energyLevel[level.idx_energyLevel]:
            buff.start(level)
        # win if beans all consumed
        if level.nbeans == 0:
            return GAME_STATE_WIN

    # Big beans
    if level.data[v][u] == L_BEAN_BIG:
        level.data[v][u] = L_EMPTY
        del level.dynamicObjects[uv_to_key([u, v])]
        level.nbeans -= 1
        score += 10
        eatman.energy += 1
        eatman.lastEatTime = time.time()
        resource.sounds['bean-big'].play()
        # eatman is now able to eat ghosts
        eatman.lastSlayerTime = time.time()
        for ghost in ghosts:
            if ghost.mode == Ghost.MODE_SCATTER or ghost.mode == Ghost.MODE_CHASE:
                ghost.oldMode = ghost.mode
                # make ghost freightened
                ghost.mode = Ghost.MODE_FREIGHTEN
                # reverse the direction
                ghost.pathway = get_opposite_direction(ghost.direction)
        # check if energy is full
        if eatman.energy > level.energyLevel[level.idx_energyLevel]:
            buff.start(level)
        # win if beans all consumed
        if level.nbeans == 0:
            return GAME_STATE_WIN

    # hit a buff
    if buff.active and buff.uvpos == [u, v]:
        resource.sounds['eatbuff'].play()
        score += 100
        level.buff_ate.append(buff.type)
        buff.apply(eatman, ghosts, fires, explosion, electric)
    
    # add life reward
    if score >= score_reward:
        nlifes += 1
        score_reward *= 2
        ftexts.append(FlashingTexts('1-up', eatman.xypos, duration=2.0))
        resource.sounds['extralife'].play()

    # Do we need decay the energy
    if time.time() - eatman.lastEatTime > level.energy_decay_time:
        eatman.energy -= 1
        eatman.lastEatTime = time.time()
        if eatman.energy < level.energyLevel[level.idx_energyLevel-1]:
            eatman.energy = level.energyLevel[level.idx_energyLevel-1]

    return gameState


def reset_after_lose(pause_duration, level, eatman, ghosts, fires, fruits, buff):
    global gameState

    gameState = GAME_STATE_NORMAL

    # eatman
    eatman.motion = Eatman.MOTION_IDLE
    eatman.direction = STATIC
    eatman.mode = Eatman.MODE_NORMAL
    eatman.idx_frame = 0
    eatman.lastAnimTime = 0
    eatman.lastEatTime = time.time()
    eatman.xypos = uv_to_xy(level.eatman_params['uvpos'])
    for key in eatman.freq_modifier.keys():
        value, stime, duration = eatman.freq_modifier[key]
        if duration > 0:
            del eatman.freq_modifier[key]

    # eatman
    for ghost in ghosts:
        ghost.motion = Ghost.MOTION_IDLE
        ghost.pathway = ''
        ghost.mode = Ghost.MODE_SCATTER
        ghost.oldMode = ghost.mode
        ghost.mode_duration = ghost.generate_mode_duration()
        ghost.nalters = 0
        ghost.lastMaTime = time.time()
        ghost.xypos = uv_to_xy(level.ghost_params[ghost.id]['uvpos'])
        ghost.direction = STATIC
        ghost.movedFrom = None
        ghost.idx_frame = 0
        ghost.lastAnimTime = time.time()
        ghost.lastIndoorTime = time.time()
        for key in ghost.freq_modifier.keys():
            value, stime, duration = ghost.freq_modifier[key]
            if duration > 0: # duration is positive means its a temporary buff
                del ghost.freq_modifier[key]

    # eliminate all the fires
    for id in range(len(fires)-1,-1,-1):
        del fires[id]

    # elinimate fruits
    for id in range(len(fruits)-1,-1,-1):
        del fruits[id]
    level.fruit_lastSpawnTime += pause_duration

    # eliminate buff (the not eaten ones)
    buff.active = False

    # level finish time
    level.stime += pause_duration
    

def draw_game_stats(level, eatman, ghosts):

    global score

    # the level
    theSurf, theRect = make_text_image(str(level.iLevel), BASICFONT, WHITE)
    theRect.center = (WINDOW_WIDTH/2, 35)
    DISPLAYSURF.blit(theSurf, theRect)

    # the score
    theSurf, theRect = make_text_image(str(score), BASICFONT, WHITE)
    theRect.bottomright = (WINDOW_WIDTH-10, 45)
    DISPLAYSURF.blit(theSurf, theRect)

    # the energy bar
    #energy = eatman.energy - level.energyLevel[level.idx_energyLevel-1] 
    #percent = energy*1.0/(level.energyLevel[level.idx_energyLevel] 
    #        - level.energyLevel[level.idx_energyLevel-1])
    #rect = copy.copy(level.rect_energy)
    #rect[2] = int(level.rect_energy[2]*percent)
    #pygame.draw.rect(DISPLAYSURF, YELLOW, rect)
    if debugit:
        DISPLAYSURF.blit(resource.buffs[level.buffs[level.idx_energyLevel-1]], 
                (WINDOW_WIDTH/2, WINDOW_HEIGHT-TILE_HEIGHT-18))

    # nlifes
    xx = 10
    for ii in range(1,nlifes):
        DISPLAYSURF.blit(eatman.frames[RIGHT][3], 
                (xx+(ii-1)*30, WINDOW_HEIGHT-1*TILE_HEIGHT-18))


def make_text_image(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def show_text_screen(text, color=WHITE, addtext='Press Space to play', checkEsc=False):
    # This function displays large text in the
    # center of the screen until a key is pressed.
    # Draw the text drop shadow
    titleSurf, titleRect = make_text_image(text, BIGFONT, GRAY)
    titleRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = make_text_image(text, BIGFONT, color)
    titleRect.center = (int(WINDOW_WIDTH / 2) - 3, int(WINDOW_HEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play" text.
    pressKeySurf, pressKeyRect = make_text_image(addtext, BASICFONT, WHITE)
    pressKeyRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2) + 180)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while True:
        keypress = check_for_key_press(checkEsc=checkEsc)
        if keypress is not None:
            break
        pygame.display.update()
        CLOCK_FPS.tick(FPS_LOW)

    return keypress


def check_for_quit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    #for event in pygame.event.get(KEYUP): # get all the KEYUP events
    #    if event.key == K_ESCAPE:
    #        terminate() # terminate if the KEYUP event was for the Esc key
    #    pygame.event.post(event) # put the other KEYUP event objects back

def check_for_key_press(checkEsc=False):
    # Go through event queue looking for a KEYUP event.
    # Grab KEYDOWN events to remove them from the event queue.
    check_for_quit()
    for event in pygame.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYDOWN:
            continue
        if event.key == K_RETURN or event.key == K_SPACE:
            return event.key
        elif checkEsc and event.key == K_ESCAPE:
            return event.key
        elif event.key == K_BACKQUOTE:
            pygame.display.iconify()
    pygame.event.clear()
    return None

def terminate():
    pygame.quit()
    sys.exit()


def get_mouse_spot(brect, (x, y)):
    x = x - brect[0] - BUTTON_GAP
    y = y - brect[1] - BUTTON_GAP

    col = x / (BUTTON_SIZE+BUTTON_GAP)
    if col<0 or col >= NBUTTON_PER_ROW:
        return None
    col_mod = x % (BUTTON_SIZE + BUTTON_GAP)
    if col_mod >= BUTTON_SIZE:
        return None

    row = y / (BUTTON_SIZE+BUTTON_GAP)
    if row< 0 or row >= NBUTTON_PER_COL:
        return None
    row_mod = y % (BUTTON_SIZE + BUTTON_GAP)
    if row_mod >= BUTTON_SIZE:
        return None

    return row, col

def draw_level_button(selsurf, brect, ii, color, txtcolor=WHITE, bsize=BUTTON_SIZE):

    row = ii / NBUTTON_PER_ROW
    col = ii % NBUTTON_PER_ROW

    sx = brect[0] + BUTTON_SIZE*col + BUTTON_GAP*(col+1)
    sy = brect[1] + BUTTON_SIZE*row + BUTTON_GAP*(row+1)
    srect = pygame.Rect(sx, sy, BUTTON_SIZE, BUTTON_SIZE)

    rect = pygame.Rect(0, 0, bsize, bsize)
    rect.center = srect.center

    pygame.draw.rect(selsurf, color, rect)
    tsurf, trect = make_text_image(str(ii+1), MIDFONT, txtcolor)
    if bsize != BUTTON_SIZE:
        sdiff = bsize - BUTTON_SIZE
        tsurf = pygame.transform.smoothscale(tsurf, (trect[2]+sdiff, trect[3]+sdiff))
        trect = tsurf.get_rect()
    trect.center = srect.center
    selsurf.blit(tsurf, trect)

    if ii+1 > hilevel:
        rect = resource.lockimg.get_rect()
        rect.center = srect.center
        selsurf.blit(resource.lockimg, rect)


def show_select_level_screen(iLevel=None):
    # this is for command line option
    if iLevel is not None:
        return iLevel

    global NBUTTON_PER_COL
    DISPLAYSURF.fill(BACKGROUND_COLOR)
    selsurf = DISPLAYSURF.copy()

    NBUTTON_PER_COL = MAX_LEVEL/4
    if MAX_LEVEL % NBUTTON_PER_ROW != 0: NBUTTON_PER_COL += 1

    w = BUTTON_SIZE*NBUTTON_PER_ROW + BUTTON_GAP*(NBUTTON_PER_ROW+1)
    h = BUTTON_SIZE*NBUTTON_PER_COL + BUTTON_GAP*(NBUTTON_PER_COL+1)

    brect = pygame.Rect(0,0,w,h)
    brect.center = (WINDOW_WIDTH/2, WINDOW_WIDTH/2)
    pygame.draw.rect(selsurf, GRAY, brect)

    tsurf, trect = make_text_image('Select a level or press Space to start from level one', 
            BASICFONT, WHITE)
    trect.center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 200)
    selsurf.blit(tsurf, trect)

    for ii in range(MAX_LEVEL):
        draw_level_button(selsurf, brect, ii, BLUE, WHITE)

    buttondown = False
    loopit = True
    bid = 0
    while loopit:
        ijpos = get_mouse_spot(brect, pygame.mouse.get_pos())
        buttonup = False
        check_for_quit()
        for event in pygame.event.get():
            if event.type == KEYUP:
                if event.key == K_RETURN or event.key == K_SPACE:
                    ijpos = (0, 0)
                    loopit = False
                elif event.key == K_ESCAPE:
                    ijpos = None
                    bid = -9999
                    loopit = False
                elif event.key == K_BACKQUOTE:
                    pygame.display.iconify()
            elif event.type == MOUSEBUTTONUP:
                buttondown = False
                buttonup = True
            elif event.type == MOUSEBUTTONDOWN:
                buttondown = True
                buttonup = False

        DISPLAYSURF.blit(selsurf, (0,0))
        if ijpos is not None:
            bid = ijpos[0]*NBUTTON_PER_ROW + ijpos[1]
            if bid < hilevel:
                if buttondown: color = CYAN
                else: color = BLUE
                if buttonup:
                    loopit = False
                draw_level_button(DISPLAYSURF, brect, bid, color, YELLOW, BUTTON_SIZE+10)

        pygame.display.update()
        CLOCK_FPS.tick(FPS_LOW)

    return bid+1


def show_pause_screen():
    pause_stime = time.time()

    backrect = pygame.Rect(3, WINDOW_HEIGHT/2-50, WINDOW_WIDTH-6, 100)
    pygame.draw.rect(DISPLAYSURF, BLACK, backrect)
    pygame.draw.rect(DISPLAYSURF, BLUE, backrect, 2)

    titleSurf, titleRect = make_text_image('PAUSE', MIDFONT, GRAY)
    titleRect.midtop = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2-40)
    DISPLAYSURF.blit(titleSurf, titleRect)

    titleSurf, titleRect = make_text_image('PAUSE', MIDFONT, WHITE)
    titleRect.midtop = (WINDOW_WIDTH/2-2, WINDOW_HEIGHT/2-40-2)
    DISPLAYSURF.blit(titleSurf, titleRect)

    #pressKeySurf, pressKeyRect = make_text_image('Press Space to continue or Esc to Quit', 
    #        BASICFONT, WHITE)
    #pressKeyRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2) + 30)
    #DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    qrect = pygame.Rect(0,0,100,30)
    qsurf = pygame.Surface((qrect[2], qrect[3])).convert()
    tsurf, trect = make_text_image('Quit', BASICFONT, WHITE)
    trect.center = qrect.center
    qsurf.blit(tsurf, trect)

    crect = pygame.Rect(0,0,100,30)
    csurf = pygame.Surface((crect[2], crect[3])).convert()
    tsurf, trect = make_text_image('Continue', BASICFONT, WHITE)
    trect.center = crect.center
    csurf.blit(tsurf, trect)

    qrect.topright = (WINDOW_WIDTH/2-40, WINDOW_HEIGHT/2+10)
    crect.topleft = (WINDOW_WIDTH/2+40, WINDOW_HEIGHT/2+10)

    buttondown = False
    loopit = True
    while loopit:
        xypos = pygame.mouse.get_pos()
        buttonup = False
        check_for_quit()
        for event in pygame.event.get():
            if event.type == KEYUP:
                keypress = event.key
                if event.key == K_RETURN or event.key == K_SPACE:
                    loopit = False
                    break
                elif event.key == K_ESCAPE:
                    loopit = False
                    break
                elif event.key == K_BACKQUOTE:
                    pygame.display.iconify()
            elif event.type == MOUSEBUTTONUP:
                buttondown = False
                buttonup = True
            elif event.type == MOUSEBUTTONDOWN:
                buttondown = True
                buttonup = False

        DISPLAYSURF.blit(qsurf, qrect)
        DISPLAYSURF.blit(csurf, crect)

        if qrect.collidepoint(xypos):
            pygame.draw.rect(DISPLAYSURF, YELLOW, qrect, 2)
            if buttonup:
                keypress = K_ESCAPE
                loopit = False
        else:
            pygame.draw.rect(DISPLAYSURF, BLUE, qrect, 2)

        if crect.collidepoint(xypos):
            pygame.draw.rect(DISPLAYSURF, YELLOW, crect, 2)
            if buttonup:
                keypress = K_SPACE
                loopit = False
        else:
            pygame.draw.rect(DISPLAYSURF, BLUE, crect, 2)

        pygame.display.update()
        CLOCK_FPS.tick(FPS_LOW)

    if keypress == K_ESCAPE:
        pause_duration = None
    else:
        pause_duration = time.time()-pause_stime
    return pause_duration

def show_endgame_screen():
    DISPLAYSURF.fill(DARKBLUE)
    tsurf, trect = make_text_image('Congradulations! You have defeated the game!', BASICFONT, YELLOW)
    trect.center = WINDOW_WIDTH/2, 100
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('EatMan v'+str(VERSION), BASICFONT, WHITE)
    trect.midright = WINDOW_WIDTH-10, WINDOW_HEIGHT - 130
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('Mama & Papa Studio', BASICFONT, WHITE)
    trect.midright = WINDOW_WIDTH-10, WINDOW_HEIGHT - 100
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('ywangd@gmail.com', BASICFONT, WHITE)
    trect.midright = WINDOW_WIDTH-10, WINDOW_HEIGHT - 70
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('2012', BASICFONT, WHITE)
    trect.midright = WINDOW_WIDTH-10, WINDOW_HEIGHT - 40
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('To our beloved Emma:', MIDFONT, PINK)
    trect.bottomleft = 20, WINDOW_HEIGHT/2 - 10
    DISPLAYSURF.blit(tsurf, trect)

    tsurf, trect = make_text_image('We love you!', BIGFONT, PINK)
    trect.midtop = WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 10
    DISPLAYSURF.blit(tsurf, trect)

    show_text_screen('', YELLOW, '', checkEsc=True) 

def show_title_screen():
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH = 504
    WINDOW_HEIGHT = 600
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    DISPLAYSURF.fill(BACKGROUND_COLOR)
    keypress = show_text_screen('EatMan', YELLOW, 'Press Space to start', checkEsc=True) 
    if keypress == K_ESCAPE:
        terminate()

def show_lose_screen():
    pause_stime = time.time()
    saveSurf = DISPLAYSURF.copy()
    global gameState
    while True:
        keypress = show_text_screen('Lose', WHITE, 'Press Space to continue', checkEsc=True)
        if keypress == K_ESCAPE:
            if show_pause_screen() is None:
                gameState = GAME_STATE_RETURN_TITLE
                return None
            else:
                DISPLAYSURF.blit(saveSurf, (0,0))
        else:
            break
    pause_duration = time.time()-pause_stime
    return pause_duration

def enter_name_screen(position):

    backrect = pygame.Rect(0, 0, WINDOW_WIDTH*0.7, WINDOW_HEIGHT*0.7)
    backrect.center = DISPLAYSURF.get_rect().center
    playerName = ''
    theSurf, theRect = make_text_image(playerName, BASICFONT, WHITE)
    theRect.center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2)
    DISPLAYSURF.blit(theSurf, theRect)
    loopit = True
    while loopit:
        check_for_quit()
        changed = False
        for event in pygame.event.get([KEYDOWN, KEYUP]):
            if event.type == KEYDOWN:
                continue
            if event.key >= K_a and event.key <= K_z:
                if len(playerName) < 10:
                    playerName += chr(event.key).upper()
                    changed = True
            elif event.key == K_BACKSPACE:
                if len(playerName) > 0:
                    playerName = playerName[:-1]
                    changed = True
            elif event.key == K_RETURN:
                loopit = False
                break
            elif event.key == K_BACKQUOTE:
                pygame.display.iconify()
        pygame.event.clear() # clear all other events

        # Background
        pygame.draw.rect(DISPLAYSURF, BLACK, backrect)
        pygame.draw.rect(DISPLAYSURF, BLUE, backrect, 2)

        theSurf, theRect = make_text_image('CONGRADULATIONS!', BASICFONT, YELLOW)
        theRect.center = (WINDOW_WIDTH/2, backrect[0]+40)
        DISPLAYSURF.blit(theSurf, theRect)
        theSurf, theRect = make_text_image('You made no. '+str(position+1)+' on the leader board.', 
                BASICFONT, YELLOW)
        theRect.center = (WINDOW_WIDTH/2, backrect[0]+70)
        DISPLAYSURF.blit(theSurf, theRect)

        theSurf, theRect = make_text_image('Please enter your name', BASICFONT, WHITE)
        theRect.center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 50)
        DISPLAYSURF.blit(theSurf, theRect)

        theSurf, theRect = make_text_image(playerName, BASICFONT, WHITE)
        theRect.center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2)
        DISPLAYSURF.blit(theSurf, theRect)

        line_start_pos = (theRect.right, theRect.bottom)
        if round(time.time()) % 2 == 0:
            pygame.draw.line(DISPLAYSURF, WHITE, 
                    line_start_pos, (line_start_pos[0]+15,line_start_pos[1]), 2)

        pygame.display.update()
        CLOCK_FPS.tick(FPS_LOW)

    if playerName == '':
        playerName = 'NONAME'

    return playerName

def show_gameover_screen():

    for ii in range(len(hsvalues)):
        if hsvalues[ii] <= score:
            playerName = enter_name_screen(ii)
            hsnames.insert(ii, playerName)
            hsvalues.insert(ii, score)
            del hsnames[-1]
            del hsvalues[-1]
            save_hiscore()
            break

    rect = pygame.Rect(0, 0, WINDOW_WIDTH*0.7, WINDOW_HEIGHT*0.7)
    rect.center = DISPLAYSURF.get_rect().center
    pygame.draw.rect(DISPLAYSURF, BLACK, rect)
    pygame.draw.rect(DISPLAYSURF, BLUE, rect, 2)

    theSurf, theRect = make_text_image('Game Over', MIDFONT, GRAY)
    theRect.center = (WINDOW_WIDTH/2, rect[0]-20) 
    DISPLAYSURF.blit(theSurf, theRect)
    theSurf, theRect = make_text_image('Game Over', MIDFONT, WHITE)
    theRect.center = (WINDOW_WIDTH/2-2, rect[0]-20-2)
    DISPLAYSURF.blit(theSurf, theRect)

    theSurf, theRect = make_text_image('Leader Board', BASICFONT, YELLOW)
    theRect.centerx = WINDOW_WIDTH/2
    theRect.top = rect[0] + 25
    DISPLAYSURF.blit(theSurf, theRect)

    # a line
    yy = rect[0] + 50
    pygame.draw.line(DISPLAYSURF, BLUE, (WINDOW_WIDTH/2-150, yy), (WINDOW_WIDTH/2+150, yy), 1)

    yy += 20
    for ii in range(len(hsvalues)):
        theSurf, theRect = make_text_image(hsnames[ii], BASICFONT, WHITE)
        theRect.midright = (WINDOW_WIDTH/2-40, yy)
        DISPLAYSURF.blit(theSurf, theRect)
        theSurf, theRect = make_text_image(str(hsvalues[ii]), BASICFONT, WHITE)
        theRect.midleft = (WINDOW_WIDTH/2+40, yy)
        DISPLAYSURF.blit(theSurf, theRect)
        yy += TILE_HEIGHT + 5

    saveSurf = DISPLAYSURF.copy()
    while True:
        keypress = show_text_screen('',WHITE,'Press Space to continue', checkEsc=True) # for key check
        if keypress == K_ESCAPE:
            if show_pause_screen() is None:
                gameState = GAME_STATE_RETURN_TITLE
                return
            else:
                DISPLAYSURF.blit(saveSurf, (0,0))
        else:
            break



def show_win_screen(level, ghosts):

    rect = pygame.Rect(0, 0, WINDOW_WIDTH*0.7, WINDOW_HEIGHT*0.7)
    rect.center = DISPLAYSURF.get_rect().center
    pygame.draw.rect(DISPLAYSURF, BLACK, rect)
    pygame.draw.rect(DISPLAYSURF, BLUE, rect, 2)

    theSurf, theRect = make_text_image('You Win', MIDFONT, GRAY)
    theRect.center = (WINDOW_WIDTH/2, rect[0]-20)
    DISPLAYSURF.blit(theSurf, theRect)
    theSurf, theRect = make_text_image('You Win', MIDFONT, YELLOW)
    theRect.center = (WINDOW_WIDTH/2-2, rect[0]-20-2)
    DISPLAYSURF.blit(theSurf, theRect)

    theSurf, theRect = make_text_image('Level Stats', BASICFONT, YELLOW)
    theRect.centerx = WINDOW_WIDTH/2
    theRect.top = rect[0] + 40
    DISPLAYSURF.blit(theSurf, theRect)

    xx = WINDOW_WIDTH/2 - 40
    yy = rect[0] + 80
    for ghost in ghosts:
        num = level.ghost_ate.count(ghost.id)
        if num > 0:
            img = ghost.frames[0].copy()
            for y in range(7, 7+3):
                for x in range (8, 8+2):
                    img.set_at((x,y), BLUE)
                    img.set_at((x+9,y), BLUE)
            DISPLAYSURF.blit(img, (xx, yy))
            theSurf, theRect = make_text_image(str(num), BASICFONT, WHITE)
            theRect.midleft = (xx+80, yy+TILE_HEIGHT/2)
            DISPLAYSURF.blit(theSurf, theRect)
            yy += TILE_HEIGHT+10

    for fruit in resource.fruits:
        num = level.fruit_ate.count(fruit)
        if num > 0:
            DISPLAYSURF.blit(fruit, (xx, yy))
            theSurf, theRect = make_text_image(str(num), BASICFONT, WHITE)
            theRect.midleft = (xx+80, yy+TILE_HEIGHT/2)
            DISPLAYSURF.blit(theSurf, theRect)
            yy += TILE_HEIGHT+10

    for buffType in BUFFS_ALL:
        num = level.buff_ate.count(buffType)
        if num > 0:
            DISPLAYSURF.blit(resource.buffs[buffType], (xx, yy))
            theSurf, theRect = make_text_image(str(num), BASICFONT, WHITE)
            theRect.midleft = (xx+80, yy+TILE_HEIGHT/2)
            DISPLAYSURF.blit(theSurf, theRect)
            yy += TILE_HEIGHT+10

    theSurf, theRect = make_text_image('Score', BASICFONT, WHITE)
    theRect.midright = (xx+TILE_WIDTH, yy+TILE_HEIGHT/2)
    DISPLAYSURF.blit(theSurf, theRect)
    theSurf, theRect = make_text_image(str(score-level.score_pre), BASICFONT, WHITE)
    theRect.midleft = (xx+80, yy+TILE_HEIGHT/2)
    DISPLAYSURF.blit(theSurf, theRect)
    yy += TILE_HEIGHT+5

    theSurf, theRect = make_text_image('Time', BASICFONT, WHITE)
    theRect.midright = (xx+TILE_WIDTH, yy+TILE_HEIGHT/2)
    DISPLAYSURF.blit(theSurf, theRect)
    nsecs = int(round(time.time()-level.stime))
    nmins = nsecs/60
    nsecs = nsecs % 60
    theSurf, theRect = make_text_image(str(nmins)+"' "+str(nsecs)+'"', BASICFONT, WHITE)
    theRect.midleft = (xx+80, yy+TILE_HEIGHT/2)
    DISPLAYSURF.blit(theSurf, theRect)
    yy += TILE_HEIGHT+5

    saveSurf = DISPLAYSURF.copy()
    global gameState
    while True:
        keypress = show_text_screen('',WHITE,'Press Space to continue', checkEsc=True)
        if keypress == K_ESCAPE:
            if show_pause_screen() is None:
                gameState = GAME_STATE_RETURN_TITLE
                return
            else:
                DISPLAYSURF.blit(saveSurf, (0,0))
        else:
            break


def save_hiscore():
    outs = open(os.path.join(SRCDIR,'hiscore.txt'),'w')
    for ii in range(len(hsvalues)):
        outs.write(hsnames[ii]+','+str(hsvalues[ii])+'\n')
    outs.close()

def save_hilevel():
    outs = open(os.path.join(SRCDIR,'hilevel.txt'),'w')
    outs.write(str(hilevel)+'\n')
    outs.close()


def pause_before_start():
    saveSurf = DISPLAYSURF.copy()

    tsurf, trect = make_text_image(str(3), BIGFONT, WHITE)
    trect.midtop = DISPLAYSURF.get_rect().center
    DISPLAYSURF.blit(tsurf, trect)
    pygame.display.update()
    time.sleep(0.6)

    tsurf, trect = make_text_image(str(2), BIGFONT, WHITE)
    trect.midtop = DISPLAYSURF.get_rect().center
    DISPLAYSURF.blit(saveSurf, (0,0))
    DISPLAYSURF.blit(tsurf, trect)
    pygame.display.update()
    time.sleep(0.6)

    tsurf, trect = make_text_image(str(1), BIGFONT, WHITE)
    trect.midtop = DISPLAYSURF.get_rect().center
    DISPLAYSURF.blit(saveSurf, (0,0))
    DISPLAYSURF.blit(tsurf, trect)
    pygame.display.update()
    time.sleep(0.6)


def main():

    global debugit, gameState, score, score_reward, DISPLAYSURF, BASICFONT, MIDFONT, BIGFONT, CLOCK_FPS, nlifes, hilevel

    pygame.init()
    CLOCK_FPS = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    MIDFONT = pygame.font.Font('freesansbold.ttf', 46)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 90)

    pygame.display.set_caption('EatMan')
    pygame.display.set_icon(
            pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-icon.png')).convert())

    resource.load_tiles()
    resource.load_sounds()
    resource.load_sprites()

    nlifes = config.get('Game','ilifes')
    score_reward = config.get('Game','iscorereward')

    # high level
    try:
        hlfile = open(os.path.join(SRCDIR,'hilevel.txt'))
        hilevel = int(hlfile.readline())
    except IOError, ValueError:
        hilevel = 1

    iLevel = None
    debugit = 0
    # optional command line arguments
    if len(sys.argv) > 1:
        for argv in sys.argv[1:]:
            if argv[0:2] == '-l':
                iLevel = int(argv[2:])
            elif argv[0:2] == '-d':
                debugit = 1

    while True:
        show_title_screen()
        iLevel = show_select_level_screen(iLevel)
        if iLevel >= 1:
            break
        else:
            iLevel = None

    while True: # game loop
        run_game(iLevel)
        if gameState == GAME_STATE_DEAD or gameState == GAME_STATE_RETURN_TITLE:
            score = 0
            nlifes = config.get('Game','ilifes')
            while True:
                show_title_screen()
                iLevel = show_select_level_screen()
                if iLevel >= 1:
                    break
        elif gameState == GAME_STATE_WIN:
            iLevel += 1
            if iLevel > MAX_LEVEL:
                show_endgame_screen()
                while True:
                    show_title_screen()
                    iLevel = show_select_level_screen()
                    if iLevel >= 1:
                        break
            elif iLevel > hilevel:
                hilevel = iLevel
                save_hilevel()


def run_game(iLevel):

    global gameState, DISPLAYSURF, WINDOW_WIDTH, WINDOW_HEIGHT, nlifes

    # Reset game status and reset the screen to black to start
    gameState = GAME_STATE_NORMAL

    # Erase the screen 
    DISPLAYSURF.fill(BACKGROUND_COLOR)

    # Load the level file
    level = Level()
    level.load(iLevel)

    # Resize the window according to the maze size
    WINDOW_WIDTH = level.ncols*TILE_WIDTH
    WINDOW_HEIGHT = (level.nrows+4)*TILE_HEIGHT
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # recolor the tiles according to the level requirement
    resource.recolor_tiles(level)
    # analyze the data to assign tiles
    level.analyze_data(DISPLAYSURF)


    # The EatMan
    eatman = Eatman(level)

    # The ghosts
    ghosts = []
    for i in range(level.nghosts):
        ghosts.append(Ghost(i, level, eatman))

    # The fires
    fires = []

    # the flashing text notices
    ftexts = []

    # The fruit
    fruits = []

    # Explosion
    explosion = Explosion()

    # The buff
    buff = Buff()

    # electric
    electric = Electric()


    # a brief wait
    level.draw(DISPLAYSURF)
    for ghost in ghosts:
        ghost.draw(DISPLAYSURF, eatman)
    eatman.draw(DISPLAYSURF)
    # Draw game state infos
    draw_game_stats(level, eatman, ghosts)
    pause_before_start()

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False    

    loopit = True
    while loopit:

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

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

                elif event.key == K_n and debugit:
                    gameState = GAME_STATE_WIN

                elif event.key == K_r and debugit:
                    gameState = GAME_STATE_RESTART

                elif event.key == K_q and debugit:
                    gameState = GAME_STATE_DYING

                elif event.key == K_b and debugit:
                    buff.active = True
                    buff.type = BUFF_BOMB
                    buff.apply(eatman, ghosts, fires, explosion, electric)

                elif event.key == K_l and debugit:
                    buff.start(level, BUFF_ELECTRIC)
                    buff.apply(eatman, ghosts, fires, explosion, electric)

                elif event.key == K_s and debugit:
                    buff.start(level, BUFF_SHIELD)
                    buff.apply(eatman, ghosts, fires, explosion, electric)

                elif event.key == K_d and debugit:
                    buff.start(level, BUFF_DAO)
                    buff.apply(eatman, ghosts, fires, explosion, electric)

                elif event.key == K_f and debugit:
                    level.fruit_lastSpawnTime = 0

                elif event.key == K_BACKQUOTE:
                    if pygame.display.iconify():
                        pygame.event.clear()
                        pygame.event.post(pygame.event.Event(KEYUP, {'key':K_ESCAPE,'mod':KMOD_NONE}))


                elif event.key == K_ESCAPE:
                    pause_duration = show_pause_screen()
                    if pause_duration is None:
                        gameState = GAME_STATE_RETURN_TITLE
                        return
                    # re-calculate important timers
                    # eatman
                    eatman.lastSlayerTime += pause_duration
                    eatman.lastEatTime += pause_duration
                    for key in eatman.freq_modifier:
                            value, stime, duration = eatman.freq_modifier[key]
                            stime += pause_duration
                            eatman.freq_modifier[key] = (value, stime, duration)
                    # ghosts
                    for ghost in ghosts:
                        ghost.lastMaTime += pause_duration
                        for key in ghost.freq_modifier:
                            value, stime, duration = ghost.freq_modifier[key]
                            stime += pause_duration
                            ghost.freq_modifier[key] = (value, stime, duration)
                    # objects
                    for fire in fires:
                        fire.stime += pause_duration
                    for ftext in ftexts:
                        ftext.stime += pause_duration
                    for fruit in fruits:
                        fruit.stime += pause_duration
                    level.fruit_lastSpawnTime += pause_duration
                    # level finish time
                    level.stime += pause_duration


        # Always change the facing direction when eatman is idle.
        # But only animate it if there is valid space to move.
        if (gameState != GAME_STATE_DYING \
                and gameState != GAME_STATE_DEAD \
                and gameState != GAME_STATE_WIN) \
                and eatman.motion == Eatman.MOTION_IDLE:

            if eatman.mode == Eatman.MODE_DAO_PASSING:
                eatman.motion = Eatman.MOTION_ANIMATE

            elif moveUp or moveDown or moveLeft or moveRight:
                if moveUp: 
                    eatman.direction = UP 
                    if is_valid_position(level, eatman, voffset=-1):
                        eatman.motion = Eatman.MOTION_ANIMATE
                elif moveDown: 
                    eatman.direction = DOWN
                    if is_valid_position(level, eatman, voffset=1):
                        eatman.motion = Eatman.MOTION_ANIMATE
                elif moveLeft:
                    eatman.direction = LEFT
                    if is_valid_position(level, eatman, uoffset=-1):
                        eatman.motion = Eatman.MOTION_ANIMATE
                elif moveRight:
                    eatman.direction = RIGHT
                    if is_valid_position(level, eatman, uoffset=1):
                        eatman.motion = Eatman.MOTION_ANIMATE

        # The regular movements
        if gameState != GAME_STATE_DYING \
                and gameState != GAME_STATE_DEAD \
                and gameState != GAME_STATE_WIN:

            # The eatman
            eatman.make_move(buff)

            # Ghosts
            for ghost in ghosts:
                ghost.make_move(level, eatman, fires)

            # Fruit
            for id in range(len(fruits)-1,-1,-1):
                if fruits[id].is_expired():
                    del fruits[id]
                else:
                    fruits[id].make_move(level)
            if len(fruits)==0 and time.time()-level.fruit_lastSpawnTime > level.fruit_interval:
                fruits.append(Fruit(level))
                level.fruit_lastSpawnTime = time.time()

            # Check if anything is hit
            gameState = check_hit(level, eatman, ghosts, 
                    fires, fruits, ftexts, explosion, buff, electric)


        # Start the drawing
        level.draw(DISPLAYSURF)

        # the fires
        for id in range(len(fires)-1, -1, -1):
            if fires[id].is_expired():
                del fires[id] 
            else:
                fires[id].animate(DISPLAYSURF)

        # fruit
        for fruit in fruits:
            fruit.draw(DISPLAYSURF)

        # buff
        buff.draw(DISPLAYSURF, eatman)

        # ghosts
        for ghost in ghosts:
            ghost.draw(DISPLAYSURF, eatman)

        # explosion
        explosion.animate(DISPLAYSURF)

        # electirc
        electric.animate(DISPLAYSURF)

        # Draw game state infos
        draw_game_stats(level, eatman, ghosts)
        
        # Dead?
        if gameState == GAME_STATE_DYING:
            gameState = eatman.animate_dead(DISPLAYSURF)
            if gameState == GAME_STATE_DEAD:
                nlifes -= 1
                if nlifes == 0:
                    time.sleep(0.5)
                    loopit = False
                else:
                    pause_duration = show_lose_screen()
                    if pause_duration is None:
                        return
                    reset_after_lose(pause_duration, level, eatman, ghosts, fires, fruits, buff)
        else:
            eatman.draw(DISPLAYSURF)

        # the flashing text notices
        for id in range(len(ftexts)-1,-1,-1):
            if ftexts[id].is_expired():
                del ftexts[id]
            else:
                ftexts[id].animate(DISPLAYSURF)

        # Win?
        if gameState == GAME_STATE_WIN:
            loopit = False

        # restart
        if gameState == GAME_STATE_RESTART:
            loopit = False
    
        # Update the actual screen image
        pygame.display.update()
        CLOCK_FPS.tick(FPS)

    # we are out of the loop 
    if gameState == GAME_STATE_WIN:
        show_win_screen(level, ghosts)
    elif gameState == GAME_STATE_DEAD:
        show_gameover_screen()



if __name__ == '__main__':

    import traceback
    try:
        main()
    except Exception as inst:
        outs = open(os.path.join(SRCDIR,'error.log'),'a+')
        traceback.print_exc(file=outs)
        outs.close()
        raise


