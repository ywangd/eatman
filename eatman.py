#!/usr/bin/env python
import os, sys, time, random, copy
import ConfigParser
import pygame
from pygame.locals import *
import pprint

SRCDIR                  = os.path.abspath(os.path.dirname(sys.argv[0]))

FPS                     = 60

WINDOW_WIDTH            = 504
WINDOW_HEIGHT           = 609

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

STATIC                  = 's'
UP                      = 'u'
DOWN                    = 'd'
LEFT                    = 'l'
RIGHT                   = 'r'

L_BLOCK                 = '#' # so no bean will be there
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

BLUE                    = (50,   50, 255, 255)
WHITE                   = (248, 248, 248, 255)
BLACK                   = (  0,   0,   0, 255)
YELLOW                  = (255, 255,   0, 255)

SLOW = 'snow'
FREEZE = 'ice'
SPEED = 'boots'
BOMB = 'bomb'
BUFFS_ALL = [SLOW, FREEZE, SPEED, BOMB]

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
        self.exploding = {}

        files = os.listdir(os.path.join(SRCDIR,'sprites'))
        for filename in files:
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

            if filename[0:-6] == 'exploding':
                self.exploding[filename[0:-4]] = pygame.image.load(
                        os.path.join(SRCDIR,'sprites',filename)).convert()


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

#################################################################################

class Level(object):

    def __init__(self):
        self.wallbgcolor = (0, 0, 0)
        self.beancolor = (255, 255, 255)
        self.wallbrightcolor = (0, 0, 255)
        self.wallshadowcolor = (0, 0, 255)

        self.nbeans = 0
        self.idx_beansound = 0

        self.eatman_params = {}

        self.nghosts = 0
        self.ghost_params = {}

        self.buffs = copy.copy(BUFFS_ALL)
        random.shuffle(self.buffs)

    def load(self, iLevel):
        self.iLevel = iLevel
        infile = open(os.path.join(SRCDIR, 'levels', str(iLevel)+'.dat'))
        self.data = []
        for line in infile.readlines():
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


    def analyze_data(self, DISPLAYSURF):

        # Create the surface to display the static objects (e.g. walls)
        self.mazeSurf = DISPLAYSURF.copy()
        # The dynamic objects including beans
        self.dynamicObjects = {}

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

        # draw other static objects
        theSurf, theRect = make_text_image('score', BASICFONT, WHITE)
        theRect.bottomright = (WINDOW_WIDTH-10, 21)
        self.mazeSurf.blit(theSurf, theRect)
        
        # The energy bar
        quarter_width = int(WINDOW_WIDTH/4.0)
        rect = [quarter_width, WINDOW_HEIGHT - 2*TILE_HEIGHT, quarter_width*2, TILE_HEIGHT]
        pygame.draw.rect(self.mazeSurf, BLUE, rect)
        rect[0] += 3
        rect[1] += 3
        rect[2] -= 6
        rect[3] -= 6
        self.rect_energy = rect
        pygame.draw.rect(self.mazeSurf, BLACK, rect)
        
        self.energyLevel = [0]
        self.energyLevel.append(int(self.nbeans/3))
        self.energyLevel.append(int(self.nbeans/1.2))
        self.energyLevel.append(self.nbeans*2)
        self.idx_energyLevel = 1

        self.energy_decay_time = 2.0



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

        return None


    def draw(self, DISPLAYSURF):

        # draw the maze
        DISPLAYSURF.blit(self.mazeSurf, [0,0])

        # draw the daynamic objects, e.g. beans
        for key in self.dynamicObjects:
            obj = self.dynamicObjects[key]
            DISPLAYSURF.blit(obj.image, uv_to_xy(obj.uvpos))


class Fire(object):

    def __init__(self, uvpos):

        self.uvpos = uvpos
        self.stime = time.time()

        self.lastAnimTime = time.time()
        self.duration = config.get('Fire','fduration') # last for how many seconds
        self.animFreq = config.get('Fire','fanimatefrequency')
        self.idx_frame = 0
        self.frame_sequence = [1,2,3,4,5,6,7,8,1]

    def animate(self, DISPLAYSURF):
        id = self.frame_sequence[self.idx_frame]
        DISPLAYSURF.blit(resource.fires['fire-'+str(id)], uv_to_xy(self.uvpos))
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

    # The pursuer is special
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
            eatman.add_freq_modifier(level.ghost_params[idx]['chilling'], 1e20)

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
    def add_freq_modifier(self, value, duration):
        if self.mode != Ghost.MODE_DEAD and self.mode != Ghost.MODE_DYING:
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
            if time.time()-eatman.lastSlayerTime > config.get('Eatman','finvincibleduration')-1.5:
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
            if time.time()-eatman.lastSlayerTime > config.get('Eatman','finvincibleduration'):
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
            if len(self.pathway) > 0:
                self.follow_pathway()
                return

            # if the ghost is dying to reset point
            if self.mode == Ghost.MODE_DYING:
                # if the ghost has reached the reset point, we make it dead
                if self.uvpos_dyingto == xy_to_uv(self.xypos):
                    self.mode = Ghost.MODE_DEAD
                    self.pathway = ''
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

                if len(self.pathway) > 0:
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
                else:
                    print 'the code shouldnt come here. something is wrong.'
                    sys.exit(1)

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

    def __init__(self, level):

        self.motion          = Eatman.MOTION_IDLE

        self.direction      = STATIC
        self.nlifes         = 3

        self.xypos = uv_to_xy(level.eatman_params['uvpos'])

        self.animFreq = config.get('Eatman', 'fanimatefrequency')
        self.speed = config.get('Eatman','ispeed')

        self.freq_modifier = {}

        self.load_sprites()
        self.idx_frame      = 0
        self.lastAnimTime = time.time()

        self.lastSlayerTime = time.time()

        self.score = 0
        self.energy = 0

        self.lastEatTime = time.time()


    def load_sprites(self):
        directions = [DOWN, LEFT, RIGHT, UP] 
        frame_sequence = [1,2,3,4,5,4,3,2,1]
        self.nframes = len(frame_sequence)

        self.frames = {}
        for direc in directions:
            self.frames[direc] = []
            for idx_frame in range(self.nframes):
                filename = os.path.join(
                        SRCDIR,'sprites','eatman-'+direc+'-'+str(frame_sequence[idx_frame])+'.gif')
                self.frames[direc].append(pygame.image.load(filename).convert())

        self.frames[STATIC] = pygame.image.load(os.path.join(SRCDIR,'sprites','eatman.gif')).convert()

        # load the game over animation
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


    def make_move(self):

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

def apply_buff(buff, eatman, ghosts, fires):

    if buff == SLOW:
        for ghost in ghosts:
            ghost.add_freq_modifier(5.0, 4.0) # slow 5 times for 4 seconds
    elif buff == FREEZE:
        for ghost in ghosts:
            ghost.add_freq_modifier(99999.9, 4.0) # slow 99999.9 times for 4 seconds
    elif buff == BOMB:
        ghost_to_die = []
        for ghost in ghosts:
            if ghost.mode != Ghost.MODE_DYING or ghost.mode != Ghost.MODE_DEAD:
                ghost_to_die.append(ghost)
        if len(ghost_to_die) > 0:
            ghost_to_die = random.choice(ghost_to_die)
            ghost_to_die.mode = ghost.MODE_DYING
    elif buff == SPEED:
        eatman.add_freq_modifier(0.3333, 5.0)



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

    if u >= level.ncols or v >=level.nrows or u <= 0 or v <= 0:
        return False

    blocks = [L_WALL, L_GHOST_DOOR]
    if isinstance(entity, Ghost) and entity.mode==Ghost.MODE_DYING:
        blocks.remove(L_GHOST_DOOR)

    if level.data[v][u] not in blocks:
        return True
    else:
        return False


def check_hit(level, eatman, ghosts, fires):

    u, v = xy_to_uv(eatman.xypos)

    # hit a ghost?
    for ghost in ghosts:
        if [u, v] == xy_to_uv(ghost.xypos):
            if ghost.mode == Ghost.MODE_FREIGHTEN:
                # eat a ghost
                ghost.mode = ghost.MODE_DYING
                eatman.lastEatTime = time.time()
                eatman.score += 100

            elif ghost.mode == Ghost.MODE_DYING or ghost.mode == Ghost.MODE_DEAD:
                pass

            else:
                # killed by a ghost
                eatman.idx_frame = 0
                return GAME_STATE_DYING

    # hit a fire?
    for fire in fires:
        if fire.uvpos == [u, v]:
            eatman.idx_frame = 0
            return GAME_STATE_DYING

    # Check if a bean is hit
    if level.data[v][u] == L_BEAN:
        level.data[v][u] = L_EMPTY
        del level.dynamicObjects[uv_to_key([u, v])]
        level.nbeans -= 1
        eatman.score += 1
        eatman.energy += 1
        eatman.lastEatTime = time.time()
        resource.sounds['bean-'+str(level.idx_beansound)].play()
        level.idx_beansound += 1
        if level.idx_beansound >=2:
            level.idx_beansound = 0
        # check if energy is full
        if eatman.energy > level.energyLevel[level.idx_energyLevel]:
            buff = level.buffs[level.idx_energyLevel-1]
            apply_buff(buff, eatman, ghosts, fires)
            level.idx_energyLevel += 1
        # win if beans all consumed
        if level.nbeans == 0:
            return GAME_STATE_WIN

    # Big beans
    if level.data[v][u] == L_BEAN_BIG:
        level.data[v][u] = L_EMPTY
        del level.dynamicObjects[uv_to_key([u, v])]
        level.nbeans -= 1
        eatman.score += 10
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
            buff = level.buffs[level.idx_energyLevel-1]
            apply_buff(buff, eatman, ghosts, fires)
            level.idx_energyLevel += 1
        # win if beans all consumed
        if level.nbeans == 0:
            return GAME_STATE_WIN

    # Do we need decay the energy
    if time.time() - eatman.lastEatTime > level.energy_decay_time:
        eatman.energy -= 1
        eatman.lastEatTime = time.time()
        if eatman.energy < level.energyLevel[level.idx_energyLevel-1]:
            eatman.energy = level.energyLevel[level.idx_energyLevel-1]

    return gameState


def draw_game_stats(level, eatman, ghosts):

    theSurf, theRect = make_text_image(str(eatman.score), BASICFONT, WHITE)
    theRect.bottomright = (WINDOW_WIDTH-10, 45)
    DISPLAYSURF.blit(theSurf, theRect)

    energy = eatman.energy - level.energyLevel[level.idx_energyLevel-1] 
    percent = energy*1.0/(level.energyLevel[level.idx_energyLevel] 
            - level.energyLevel[level.idx_energyLevel-1])
    rect = copy.copy(level.rect_energy)
    DISPLAYSURF.blit(resource.buffs[level.buffs[level.idx_energyLevel-1]], 
            [rect[0]+rect[2]+10, rect[1]])
    rect[2] = int(level.rect_energy[2]*percent)
    pygame.draw.rect(DISPLAYSURF, YELLOW, rect)


def make_text_image(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def show_text_screen(text, color=WHITE):
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

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = make_text_image('Press Enter to play.', BASICFONT, WHITE)
    pressKeyRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while check_for_key_press() == None:
        pygame.display.update()

    CLOCK_FPS.tick(FPS)


def check_for_quit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    #for event in pygame.event.get(KEYUP): # get all the KEYUP events
    #    if event.key == K_ESCAPE:
    #        terminate() # terminate if the KEYUP event was for the Esc key
    #    pygame.event.post(event) # put the other KEYUP event objects back

def check_for_key_press():
    # Go through event queue looking for a KEYUP event.
    # Grab KEYDOWN events to remove them from the event queue.
    check_for_quit()
    for event in pygame.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYDOWN:
            continue
        if event.key == K_RETURN:
            return event.key
    return None

def terminate():
    pygame.quit()
    sys.exit()


def show_pause_screen():
    show_text_screen('PAUSE')

def show_title_screen():
    show_text_screen('EatMan', color=YELLOW)

def show_lose_screen():
    show_text_screen('Lose')

def show_win_screen():
    show_text_screen('Win')


def main():

    global gameState, DISPLAYSURF, BASICFONT, BIGFONT, CLOCK_FPS

    pygame.init()
    CLOCK_FPS = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
    pygame.display.set_caption('EatMan')
    pygame.display.set_icon(
            pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-icon.png')).convert())

    resource.load_tiles()
    resource.load_sounds()
    resource.load_sprites()

    iLevel = 0 if len(sys.argv)==1 else int(sys.argv[1])
    show_title_screen()
    while True: # game loop
        run_game(iLevel)
        if gameState == GAME_STATE_DEAD:
            show_lose_screen()
        elif gameState == GAME_STATE_WIN:
            show_win_screen()
            # advance level here?


def run_game(iLevel):

    global gameState, DISPLAYSURF, WINDOW_WIDTH, WINDOW_HEIGHT

    # Reset game status and reset the screen to black to start
    gameState = GAME_STATE_NORMAL

    # Erase the screen 
    DISPLAYSURF.fill(BACKGROUND_COLOR)

    # Load the level file
    level = Level()
    level.load(iLevel)

    # Resize the window according to the maze size
    WINDOW_WIDTH = level.ncols*TILE_WIDTH
    WINDOW_HEIGHT = (level.nrows+5)*TILE_HEIGHT
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

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False    

    loopit = True
    while loopit:

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
                    pause_stime = time.time()
                    show_pause_screen()
                    pause_duration = time.time()-pause_stime
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


        # Always change the facing direction when eatman is idle.
        # But only animate it if there is valid space to move.
        if (gameState != GAME_STATE_DYING \
                and gameState != GAME_STATE_DEAD \
                and gameState != GAME_STATE_WIN) \
                and (moveUp or moveDown or moveLeft or moveRight) \
                and eatman.motion == Eatman.MOTION_IDLE:
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
            eatman.make_move()

            # Ghosts
            for ghost in ghosts:
                ghost.make_move(level, eatman, fires)

            # Check if anything is hit
            gameState = check_hit(level, eatman, ghosts, fires)


        # Start the drawing
        level.draw(DISPLAYSURF)

        for id in range(len(fires)-1, -1, -1):
            if fires[id].is_expired():
                del(fires[id]) 
            else:
                fires[id].animate(DISPLAYSURF)

        for ghost in ghosts:
            ghost.draw(DISPLAYSURF, eatman)

        # Dead?
        if gameState == GAME_STATE_DYING:
            gameState = eatman.animate_dead(DISPLAYSURF)
            if gameState == GAME_STATE_DEAD:
                time.sleep(1)
                loopit = False
        else:
            eatman.draw(DISPLAYSURF)

        # Draw game state infos
        draw_game_stats(level, eatman, ghosts)
        
        # Win?
        if gameState == GAME_STATE_WIN:
            time.sleep(1)
            loopit = False
    
        # Update the actual screen image
        pygame.display.update()

        #CLOCK_FPS.tick(FPS)


if __name__ == '__main__':

    main()


