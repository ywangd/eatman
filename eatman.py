#!/usr/bin/env python

import os, sys, time, random, copy
import ConfigParser
import pygame
from pygame.locals import *
import pprint
import pathfinder

SRCDIR                  = os.path.abspath(os.path.dirname(sys.argv[0]))

FPS                     = 60

WINDOW_WIDTH            = 800
WINDOW_HEIGHT           = 752

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
pf = pathfinder.Pathfinder()

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

    def load(self, ilevel):
        infile = open(os.path.join(SRCDIR, 'levels', str(ilevel)+'.dat'))
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
        #
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
                    x, y = uv_to_xy((u,v))
                    rect = [x, y, TILE_WIDTH, TILE_HEIGHT]
                    self.mazeSurf.blit(img, rect)

                # If it is a bean
                elif tileRes is not None and tileRes[0][0:4] == 'bean':
                    img = resource.tiles[tileRes[0]]
                    self.dynamicObjects[uv_to_key((u,v))] = Bean((u,v), img)


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
            DISPLAYSURF.blit(obj.image, uv_to_xy(obj.pos))


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

    IDLE      = 1
    ANIMATE   = 2
    DYING     = 4

    def __init__(self, idx, level, eatman):

        self.state = Ghost.IDLE
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

        self.u_dyingto, self.v_dyingto = level.ghost_params[0]['xy']

        self.targetX = 0
        self.targetY = 0


    def set_state(self, adds):
        self.state |= adds

        if adds & Ghost.IDLE:
            self.state &= ~Ghost.ANIMATE
        elif adds & Ghost.ANIMATE:
            self.state &= ~Ghost.IDLE

    def unset_state(self, dels):
        self.state &= ~dels


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

        if self.state & Ghost.DYING:
            img = resource.glasses['glasses']

        elif not (eatman.state & Eatman.INVICIBLE):

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
            # draw eye balls
            for y in range(self.pupil_pos[1], self.pupil_pos[1]+3):
                for x in range(self.pupil_pos[0], self.pupil_pos[0]+2):
                    img.set_at((x,y), self.pupil_color)
                    img.set_at((x+9,y), self.pupil_color)

        else:
            idx_frame = self.idx_frame % len(resource.ghost_freighten) + 1
            img = resource.ghost_freighten['ghost-freighten-'+str(idx_frame)]
            if time.time()-eatman.lastInvicibleTime > config.get('Eatman','finvincibleduration')-1.5:
                if idx_frame % 2 == 0:
                    img = resource.ghost_recover['ghost-freighten-'+str(idx_frame)]
                    
        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]
        DISPLAYSURF.blit(img, rect)


    def make_move(self, level, eatman, fires):

        animFreq = self.animFreq

        if eatman.state & Eatman.INVICIBLE and not (self.state & Ghost.DYING):
            animFreq *= 3.0

        if self.state & Ghost.DYING:
            animFreq /= 4.0

        # If it is in middle of an animation, keep doint it till the cycle is done.
        if self.state & Ghost.ANIMATE and time.time()-self.lastAnimTime>animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.set_state(Ghost.IDLE)
                self.nsteps_move_cycle += 1
                self.moved_from = get_opposite_direction(self.direction)
                # drop fire
                if self.moltenPercent>0 and len(fires)<config.get('Fire','imaxfire') \
                        and random.randint(1,100)<self.moltenPercent:
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
        if self.state & Ghost.IDLE:

            if self.state & Ghost.DYING:
                su, sv = xy_to_uv((self.x, self.y))
                if su==self.u_dyingto and sv==self.v_dyingto:
                    self.unset_state(Ghost.DYING)
                    self.pathway = ''
                else:
                    self.pathway = pf.simplepath(level, self, (sv, su), 
                            (self.v_dyingto, self.u_dyingto), is_valid_position)

            elif len(self.pathway) > 0: # if there is a existing pathway
                # re-roll the strategy if it is expired
                if self.nsteps_move_cycle > self.max_step_move_cycle:
                    self.nsteps_move_cycle = 0
                    if random.randint(1,100) <= self.seekerPercent:
                        self.move_strategy = 'seeker'
                        su, sv = xy_to_uv((self.x, self.y))
                        eu, ev = xy_to_uv((eatman.x, eatman.y))
                        self.pathway = pf.astarpath((sv, su), (ev, eu))
                        self.targetX = eu
                        self.targetY = ev
                    else:
                        self.move_strategy = 'random'
                        self.pathway = pf.randpath(level, self, eatman, is_valid_position)

                if self.move_strategy == 'seeker':
                    u, v = xy_to_uv((eatman.x, eatman.y))
                    if self.targetX == u or self.targetY == v \
                            or ((self.targetX-u)**2+(self.targetY-v)**2)<18:
                        pass
                    else:
                        su, sv = xy_to_uv((self.x, self.y))
                        eu, ev = xy_to_uv((eatman.x, eatman.y))
                        self.pathway = pf.astarpath((sv, su), (ev, eu))
                        self.targetX = eu
                        self.targetY = ev

            else: # if no existing pathway
                if self.nsteps_move_cycle > self.max_step_move_cycle or self.move_strategy == '':
                    self.nsteps_move_cycle = 0
                    # re-roll the strategy
                    if random.randint(1,100) <= self.seekerPercent: # seek it
                        self.move_strategy = 'seeker'
                        su, sv = xy_to_uv((self.x, self.y))
                        eu, ev = xy_to_uv((eatman.x, eatman.y))
                        self.pathway = pf.astarpath((sv, su), (ev, eu))
                        self.targetX = eu
                        self.targetY = ev
                    else: # random path
                        self.move_strategy = 'random'
                        self.pathway = pf.randpath(level, self, eatman, is_valid_position)
                else:
                    if self.move_strategy == 'seeker':
                        su, sv = xy_to_uv((self.x, self.y))
                        eu, ev = xy_to_uv((eatman.x, eatman.y))
                        self.pathway = pf.astarpath((sv, su), (ev, eu))
                        self.targetX = eu
                        self.targetY = ev
                    elif self.move_strategy == 'random':
                        self.pathway = pf.randpath(level, self, eatman, is_valid_position)

            # now follow the pathway
            self.follow_pathway()


    def follow_pathway(self):
        if len(self.pathway) > 0:
            moveto = self.pathway[0]
            self.pathway = self.pathway[1:]
            self.set_state(Ghost.ANIMATE)
            self.direction = moveto
        else:
            self.set_state(Ghost.IDLE)
            self.direction = STATIC


class Eatman(object):
    '''
    The Eatman class for managing the Player.
    '''

    IDLE         = 1
    ANIMATE      = 2
    INVICIBLE     = 4

    def __init__(self, level):

        self.state          = Eatman.IDLE

        self.direction      = STATIC
        self.nlifes         = 3

        self.x, self.y = uv_to_xy(level.eatman_params['xy'])

        self.animFreq = config.get('Eatman', 'fanimatefrequency')
        self.speed = config.get('Eatman','ispeed')

        self.animFreq_factors = {}

        self.load_sprites()
        self.idx_frame      = 0
        self.lastAnimTime = time.time()

        self.lastInvicibleTime = time.time()

    def set_state(self, adds):
        self.state |= adds

        if adds & Eatman.IDLE:
            self.state &= ~Eatman.ANIMATE
        elif adds & Eatman.ANIMATE:
            self.state &= ~Eatman.IDLE

    def unset_state(self, dels):
        self.state &= ~dels


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

        # load the game over animation
        self.frames_dead = []
        self.frames_dead.append(pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-u-5.gif')).convert())
        for idx in range(1,9):
            self.frames_dead.append(
                    pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-dead-'+str(idx)+'.gif')).convert())


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
        if self.state & Eatman.ANIMATE and time.time()-self.lastAnimTime>animFreq:
            self.idx_frame += 1
            if self.idx_frame >= self.nframes:
                self.idx_frame = 0
                self.set_state(Eatman.IDLE)
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

    def animate_dead(self, DISPLAYSURF):

        rect = [self.x, self.y, TILE_WIDTH, TILE_HEIGHT]

        # Animate it
        if time.time()-self.lastAnimTime>self.animFreq*4.0:
            self.idx_frame += 1
            self.lastAnimTime = time.time()
            if self.idx_frame >= len(self.frames_dead):
                self.idx_frame = 0
                return GAME_STATE_DEAD

        # drawing
        DISPLAYSURF.blit(self.frames_dead[self.idx_frame], rect)

        return GAME_STATE_DYING

class Bean(object):
    def __init__(self, (u, v), image):
        self.pos = (u, v)
        self.image = image


def uv_to_key((u, v)):
    '''
    Create a dictionary key using the u, v grid cell coordinates
    '''
    return str(u) + ',' + str(v)


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

    if x >= level.ncols or y >=level.nrows or x <= 0 or y <= 0:
        return False

    if level.data[y][x] not in [L_WALL,]:
        return True
    else:
        return False


def check_hit(level, eatman, ghosts, fires):

    x, y = xy_to_uv((eatman.x, eatman.y))

    for ghost in ghosts:
        gx, gy = xy_to_uv((ghost.x, ghost.y))
        if x==gx and y==gy:
            if eatman.state & Eatman.INVICIBLE:
                ghost.set_state(Ghost.DYING)
            elif ghost.state & Ghost.DYING:
                pass
            else:
                eatman.idx_frame = 0
                return GAME_STATE_DYING

    for fire in fires:
        if x==fire.u and y==fire.v:
            eatman.idx_frame = 0
            return GAME_STATE_DYING

    # Check if a bean is hit
    if level.data[y][x] == L_BEAN:
        level.data[y][x] = L_EMPTY
        del level.dynamicObjects[uv_to_key((x,y))]
        level.nbeans -= 1
        resource.sounds['bean-'+str(level.idx_beansound)].play()
        level.idx_beansound += 1
        if level.idx_beansound >=2:
            level.idx_beansound = 0
        if level.nbeans == 0:
            return GAME_STATE_WIN

    # Big beans
    if level.data[y][x] == L_BEAN_BIG:
        level.data[y][x] = L_EMPTY
        del level.dynamicObjects[uv_to_key((x,y))]
        level.nbeans -= 1
        resource.sounds['bean-big'].play()
        if level.nbeans == 0:
            return GAME_STATE_WIN

        eatman.set_state(Eatman.INVICIBLE)
        eatman.lastInvicibleTime = time.time()

    return gameState


def make_text_image(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def show_text_screen(text):
    # This function displays large text in the
    # center of the screen until a key is pressed.
    # Draw the text drop shadow
    titleSurf, titleRect = make_text_image(text, BIGFONT, GRAY)
    titleRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = make_text_image(text, BIGFONT, WHITE)
    titleRect.center = (int(WINDOW_WIDTH / 2) - 3, int(WINDOW_HEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = make_text_image('Press a key to play.', BASICFONT, WHITE)
    pressKeyRect.center = (int(WINDOW_WIDTH / 2), int(WINDOW_HEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while check_for_key_press() == None:
        pygame.display.update()


def check_for_quit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back

def check_for_key_press():
    # Go through event queue looking for a KEYUP event.
    # Grab KEYDOWN events to remove them from the event queue.
    check_for_quit()
    for event in pygame.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYDOWN:
            continue
        return event.key
    return None

def terminate():
    pygame.quit()
    sys.exit()


def show_pause_screen():
    pass

def show_title_screen():
    show_text_screen('EatMan')

def show_lose_screen():
    show_text_screen('Lose')

def show_win_screen():
    show_text_screen('Win')


def main():

    global gameState, DISPLAYSURF, BASICFONT, BIGFONT

    pygame.init()
    #clock_fps = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
    pygame.display.set_caption('EatMan')
    pygame.display.set_icon(
            pygame.image.load(os.path.join(SRCDIR,'sprites','eatman-icon.png')).convert())

    resource.load_tiles()
    resource.load_sounds()
    resource.load_sprites()

    idx_level = 0
    show_title_screen()
    while True: # game loop
        run_game(idx_level)
        if gameState == GAME_STATE_DEAD:
            show_lose_screen()
        elif gameState == GAME_STATE_WIN:
            show_win_screen()
            # advance level here?


def run_game(idx_level):

    global gameState
    # Reset game status and reset the screen to black to start
    gameState = GAME_STATE_NORMAL
    DISPLAYSURF.fill(BACKGROUND_COLOR)

    # Load the level file
    level = Level()
    level.load(idx_level)
    # recolor the tiles according to the level requirement
    resource.recolor_tiles(level)
    # analyze the data to assign tiles
    level.analyze_data(DISPLAYSURF)

    # Initialize the pathfinder map
    pf.init_map(level, L_WALL)

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
                    show_pause_screen()

        # Always change the facing direction when eatman is idle.
        # But only animate it if there is valid space to move.
        if (gameState != GAME_STATE_DYING \
                and gameState != GAME_STATE_DEAD \
                and gameState != GAME_STATE_WIN) \
                and (moveUp or moveDown or moveLeft or moveRight) \
                and eatman.state & Eatman.IDLE:
            if moveUp: 
                eatman.direction = UP 
                if is_valid_position(level, eatman, yoffset=-1):
                    eatman.set_state(Eatman.ANIMATE)
            elif moveDown: 
                eatman.direction = DOWN
                if is_valid_position(level, eatman, yoffset=1):
                    eatman.set_state(Eatman.ANIMATE)
            elif moveLeft:
                eatman.direction = LEFT
                if is_valid_position(level, eatman, xoffset=-1):
                    eatman.set_state(Eatman.ANIMATE)
            elif moveRight:
                eatman.direction = RIGHT
                if is_valid_position(level, eatman, xoffset=1):
                    eatman.set_state(Eatman.ANIMATE)

        if gameState != GAME_STATE_DYING \
                and gameState != GAME_STATE_DEAD \
                and gameState != GAME_STATE_WIN:
            # Movements
            eatman.make_move()
            for ghost in ghosts:
                ghost.make_move(level, eatman, fires)
            # Check if anything is hit
            gameState = check_hit(level, eatman, ghosts, fires)

        if eatman.state & Eatman.INVICIBLE:
            if time.time()-eatman.lastInvicibleTime > config.get('Eatman','finvincibleduration'):
                eatman.unset_state(Eatman.INVICIBLE)

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
                time.sleep(2)
                loopit = False
        else:
            eatman.draw(DISPLAYSURF)
        
        # Win?
        if gameState == GAME_STATE_WIN:
            time.sleep(2)
            loopit = False
    
        # Update the actual screen image
        pygame.display.update()

        #clock_fps.tick(FPS)


if __name__ == '__main__':

    main()


