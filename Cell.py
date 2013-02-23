from Generic import *
from ordereddict import OrderedDict
import Pin

class Cell(Generic):
    "Defines an instantiated Cell"

    def __init__(self, attrs):
        Generic.__init__(self, attrs)

        self.__submodname = self.get("submodname")

        # to be linked
        self.__pins = OrderedDict()
        self.__submod = None

    def __eq__(self, other):

	def bool_pins():
	    if len(self.__pins) != len(other.pins):
	    	return False

	    return cmp(sorted(self.__pins.keys()), sorted(other.pins.keys())) == 0

###	if [i for i in self.__pins

#    def __gt__(self, other):

#    def __lt__(self, other):

    pins       = property(lambda self: self.__pins)
    submodname = property(lambda self: self.__submodname)
    submod     = property(lambda self: self.__submod)

    def new_pin(self, pinAttr):
        pinAttr["cell"] = self
        pinAttr["module"] = self.module
        # create new pin here
        pin = Pin.Pin(pinAttr)
        self.__pins[pin.name] = pin
        return pin

    def linkMod(self, mod):
        #if self.__submod != None:
        #    print "Warning: " + self.name + " multiply linked"
        self.__submod = mod
