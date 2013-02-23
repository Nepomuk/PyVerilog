
from Netlist import *
import yaml
import os
import Module
import Cell

class ECO(Netlist):
    """
    Add new ECO cell in org NetList file.
    >>> eco = ECO()
    >>> eco.readYAML("test/gates.yml") # read cell libs
    >>> eco.readVerilog("test/Iface_test.gv") # read org verilog Netlist file
    >>> eco.link("Iface_test") # link top module
    >>> eco.checkDesign() # check pre load design is ok
    >>> eco.report()
    >>> eco.readECO("test/ECO.yml") # read eco file
    >>> eco.runECO() # run eco
    >>> eco.checkDesign() # recheck design again when the ECO is done
    >>> eco.report()
    >>> eco.writeVerilog("test/new_Iface_test.gv")
    """

    eco = property(lambda self: self.__eco)

    def __init__(self):
	super(ECO,self).__init__()
	self.__eco = {}

    def readECO(self, ecoFile):
	""" read eco file """
        file = open(ecoFile)
        nl = yaml.safe_load(file)
        file.close()

        self.__eco.update(nl)

    def runECO(self):
    	""" add ECO cell """

	submodname = self.__eco.keys()[0]
	name = 'ECO_' + submodname
	module = self.mods[self.topMod]

	cell = module.new_cell({ "name" : name, "submodname": submodname })

	for pinName, netName in self.__eco[submodname]['inputs'].items():

	    # ECO cell assign 0, 1 to new pin link
	    if not module.nets.has_key(netName):
	    	if netName not in [0, 1]:
		   raise Exception("%s doesn't have net %s" %(self.topMod, netName))

		new_net = module.new_net({ "name":netName, "width":1, "busMember":False, "bitIdx":None,   "busName":None    })
		pin = cell.new_pin({"name":pinName, "portname":pinName})
		pin.connectNet(new_net)

	    # ECO cell cut the org link to new link
	    else:
	    	net = module.nets[netName]
		pin = cell.new_pin({"name":pinName, "portname":pinName})
		pin.connectNet(net)

		# clear all net fainouts, and create new net to build up new fanout

	for pinName, netNames in self.__eco[submodname]['outputs'].items():

	    for netName in netNames.split(','):
		if not module.nets.has_key(netName):
		   raise Exception("%s doesn't have net %s" %(self.topMod, netName))

		netName = "ECO_0"
		new_net = module.new_net({ "name":netName, "width":1, "busMember":False, "bitIdx":None,   "busName":None    })
		pin = cell.new_pin({"name":pinName, "portname":pinName})
		pin.connectNet(new_net)

		for fout in net.fanout:
		    fout.connectNet(new_net)


    def report(self):
    	pass

################################################################################
################################################################################
if __name__ == "__main__":
    import doctest
    doctest.testmod()
