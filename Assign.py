
#from Generic import *
from Net import *

class Assign(Net):

    "Defines a Verilog Module Assign"
    def __init__(self, attrs):
        Net.__init__(self, attrs)

        # to be linked later
        self.__net = None

    net       = property(lambda self: self.__net)

