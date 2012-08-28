#!/usr/bin/env python
import random

STATIC                  = 's'
UP                      = 'u'
DOWN                    = 'd'
LEFT                    = 'l'
RIGHT                   = 'r'

class Pathfinder(object):

    NODE_TYPE_UNINITIALED   = -1
    NODE_TYPE_NOT_VISITED   = 0
    NODE_TYPE_BLOCKED       = 1
    NODE_TYPE_START         = 2
    NODE_TYPE_END           = 3
    NODE_TYPE_CURRENT       = 4

    HIGH_COST               = 1e20

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


    def simplepath(self, level, ghost, (sv, su), (ev, eu), pos_check_func):
        
        moveto = [UP, LEFT, DOWN, RIGHT]

        if ghost.moved_from == UP or (not pos_check_func(level, ghost, yoffset=-1)):
            moveto.remove(UP)
        if ghost.moved_from == DOWN or (not pos_check_func(level, ghost, yoffset=1)):
            moveto.remove(DOWN)
        if ghost.moved_from == LEFT or (not pos_check_func(level, ghost, xoffset=-1)):
            moveto.remove(LEFT)
        if ghost.moved_from == RIGHT or (not pos_check_func(level, ghost, xoffset=1)):
            moveto.remove(RIGHT)

        if len(moveto) == 0:
            return ghost.moved_from

        print eu, ev
        mindist = Pathfinder.HIGH_COST
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
                print mt, dist
                mindist = dist
                choice = mt

        print moveto, choice
        return choice


    def randpath(self, level, ghost, eatman, pos_check_func):
        moveto = [UP, LEFT, DOWN, RIGHT]
        if ghost.moved_from == UP or (not pos_check_func(level, ghost, yoffset=-1)):
            moveto.remove(UP)
        if ghost.moved_from == DOWN or (not pos_check_func(level, ghost, yoffset=1)):
            moveto.remove(DOWN)
        if ghost.moved_from == LEFT or (not pos_check_func(level, ghost, xoffset=-1)):
            moveto.remove(LEFT)
        if ghost.moved_from == RIGHT or (not pos_check_func(level, ghost, xoffset=1)):
            moveto.remove(RIGHT)

        if len(moveto) == 0:
            return ghost.moved_from

        return random.choice(moveto)


    def astarpath(self, (sv, su), (ev, eu)):

        self.clear_temp_vars()
        
        # (row, col) tuples
        self.spos = (sv, su)
        self.epos = (ev, eu)

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

    def init_map(self, level, blocks):
        self.map = {}
        self.size = (level.nrows, level.ncols)

        # initialize path_finder map to a 2D array of empty nodes
        for row in range(0, self.size[0], 1):
            for col in range(0, self.size[1], 1):

                self.set_node( (row, col), self.create_new_node() )

                if level.data[row][col] in list(blocks):
                    self.set_type((row, col), Pathfinder.NODE_TYPE_BLOCKED)
                else:
                    self.set_type((row, col), Pathfinder.NODE_TYPE_NOT_VISITED)

    def create_new_node(self):
        node = {}
        node['g'] = -1
        node['h'] = -1
        node['f'] = -1
        node['parent'] = (-1, -1)
        node['type'] = Pathfinder.NODE_TYPE_UNINITIALED
        return node

    def unfold (self, (row, col)):
        # this function converts a 2D array coordinate pair (row, col)
        # to a 1D-array index, for the object's 1D map array.
        return (row * self.size[1]) + col
    
    def set_node (self, (row, col), newNode):
        # sets the value of a particular map cell (usually refers to a node object)
        self.map[ self.unfold((row, col)) ] = newNode
        
    def get_type (self, (row, col)):
        return self.map[ self.unfold((row, col)) ]['type']
        
    def set_type (self, (row, col), theType):
        self.map[ self.unfold((row, col)) ]['type'] = theType

    def getF (self, (row, col)):
        return self.map[ self.unfold((row, col)) ]['f']

    def getG (self, (row, col)):
        return self.map[ self.unfold((row, col)) ]['g']
    
    def getH (self, (row, col)):
        return self.map[ self.unfold((row, col)) ]['h']
        
    def setG (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ]['g'] = newValue

    def setH (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ]['h'] = newValue
        
    def setF (self, (row, col), newValue ):
        self.map[ self.unfold((row, col)) ]['f'] = newValue
        
    def calcH (self, (row, col)):
        self.setH( (row, col), abs(row - self.epos[0]) + abs(col - self.epos[0]) )
        
    def calcF (self, (row, col)):
        self.setF( (row, col), self.getG((row,col)) + self.getH((row,col)) )
    
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
        lowestValue = Pathfinder.HIGH_COST # start arbitrarily high
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
        self.map[ self.unfold((row, col)) ]['parent'] = (parentRow, parentCol)

    def get_parent (self, (row, col) ):
        return self.map[ self.unfold((row, col)) ]['parent']
        
    def clear_temp_vars (self):
        # this resets variables needed for a search (but preserves the same map / maze)
        self.pathChainRev = ''
        self.pathChain = ''
        self.current = (-1, -1)
        self.openlist = []
        self.closelist = []

