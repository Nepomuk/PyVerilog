from Generic import *

class Net(Generic):
    "A Verilog net"
    def __init__(self, attrs):
        Generic.__init__(self, attrs)

        self.__width = self.get("width")
        self.__msb = self.get("msb", require=False)
        self.__lsb = self.get("lsb", require=False)
        self.__busMember = self.get("busMember")
        self.__busName = self.get("busName")
        self.__bitIdx  = self.get("bitIdx")
	self.__module = self.get('module')

        if self.__width > 1:
            if self.__msb == None or self.__lsb == None:
                print "Warning: using default msb/lsb for " + self.name
                self.__msb = self.__width-1
                self.__lsb = 0
                #raise Exception("width without msb and lsb")

        if self.__msb != None and self.__lsb != None:
            if self.__msb - self.__lsb + 1 != self.__width:
                raise Exception("inconsistent msb and lsb")


        #to be linked
        self.__fanin = []
        self.__fanout = []

    def __eq__(self, other):
    	bool_width = self.__width == other.width
        bool_msb   = self.__msb   == other.msb
    	bool_lsb   = self.__lsb   == other.lsb
	bool_bitIdx= self.__bitIdx == other.bitIdx
	bool_busName = self.__busName == other.busName
	bool_busMember = self.__busMember == other.busMember
	bool_module = self.__module == other.module

	def cmp_fanin():
	    if len(self.__fanin) != len(other.fanin):
	    	return False
	    else:
		self_fanin = sorted([i.net.portname for i in self.__fanin])
		other_fanin = sorted([i.net.portname for i in other.fanin])
		return cmp(self_fanin, other_fanin) == 0

	def cmp_fanout():
	    if len(self.__fanout) != len(other.fanout):
	    	return False
	    else:
		self_fanout = sorted([i.net.portname for i in self.__fanin])
		other_fanout = sorted([i.net.portname for i in other.fanin])
		return cmp(self_fanout, other_fanout) == 0

	bool_fanin = cmp_fanin()
	bool_fanout = conp_fanout()

	if bool_fanout and \
	   bool_fanin and \
	   bool_width and \
	   bool_msb and \
	   bool_lsb and \
	   bool_bitIdx and \
	   bool_busName and \
	   bool_module:
	       return True
	return False

    width   = property(lambda self: self.__width)
    msb     = property(lambda self: self.__msb)
    lsb     = property(lambda self: self.__lsb)
    fanin   = property(lambda self: self.__fanin)
    fanout  = property(lambda self: self.__fanout)
    bitIdx  = property(lambda self: self.__bitIdx)
    busName = property(lambda self: self.__busName)
    busMember = property(lambda self: self.__busMember)
    module = property(lambda self: self.__module)

    def setFanin(self, pin):
    	""" input only has one input drive, no multi ports to one """
        if pin in self.__fanin:
            raise Exception("different fanin already set on net " + self.name)
        self.__fanin.append(pin)

    def addFanout(self, pin):
    	""" output can have one or multi ports drive """
        self.__fanout.append(pin)

#    def setModule(self, module):
#    	""" set it's belong module """
#    	self.__module = module




