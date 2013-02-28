
from Netlist import *
import yaml
import os
import Module
import Cell
import Port
import PortIn
import PortOut
import Net
import logging

logging.basicConfig(filename='ECO.log',level=logging.DEBUG)

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

    def __init__(self):
	super(ECO,self).__init__()
	self.__eco = {}
	self.__module = None
	self.__ecocell = None
	self.__ecoinputs = []
	self.__ecooutputs = []
	self.__ecoid = 0


    def readECO(self, ecoFile):
	""" read eco file """
        file = open(ecoFile)
        nl = yaml.safe_load(file)
        file.close()

        self.__eco.update(nl)

    def _findInputObjs(self):
        """ find input obj map table
	return port, pin obj type
        """
        objs = []
	eco_modname = self.__eco.keys()[0]
        for eco_pinName, patch_hierName in self.__eco[eco_modname]['inputs'].items():
	   objs.append((eco_pinName, patch_hierName, self.deepobj(patch_hierName, dtype="port")))
        return objs

    def _findOutPutObjs(self):
        """ find output obj map table
        return port, pin obj type
        """
        objs = []
        eco_modname = self.__eco.keys()[0]
        for eco_pinName, patch_hierNames in self.__eco[eco_modname]['outputs'].items():
	    for patch_hierName in patch_hierNames.split(','):
	    	objs.append((eco_pinName, patch_hierName, self.deepobj(patch_hierName, dtype="port")))
        return objs

    def _findInputMaps(self):
        """ collect inputs when the inputs are alreasy define in org Netlist.
        otherwise create new Pin, Port, fanout """
        for eco_pinName, patch_hierName, patch_obj in self._findInputObjs():
            if not patch_obj:
		if patch_hierName in [0, 1]:
		    ass_net = self.__module.new_net({ "name":patch_hierName, "width":1, "busMember":False,  "bitIdx":None, "busName":None })
		    new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		    new_pin.connectNet(ass_net)
		    ass_net.addFanout(new_pin)
		    logging.debug("create new net %s in %s module" %(patch_hierName, self.__module.name))
		else:
		    new_port = self.__module.add_port(PortIn.PortIn({ "name": patch_hierName, "width": 1, "module":self.__module.name, "busMember":False, "bitIdx":None, "busName":None }))
		    new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		    new_pin.connectPort(new_port)
		    new_port.addFanout(new_pin)
		    logging.debug("create new input port %s in %s module" %(patch_hierName, self.__module.name))
	    else:
	    	self.__ecoinputs.append((eco_pinName, patch_obj))
		logging.debug("find InputMaps eco cell pin %s, %s" %(eco_pinName, patch_obj))


    def _findOutPutMaps(self):
        """ collect output when the output is alreasy define in org Netlist.
        otherwise create new Pin, Port, fanin
        """
        for eco_pinName, patch_hierName, patch_obj in self._findOutPutObjs():
            if not patch_obj:
		if self.__module.ports.has_key(patch_hierName):
		    new_port = self.__module.ports[patch_hierName]
		else:
		    new_port = self.__module.add_port(PortOut.PortOut({ "name": patch_hierName, "width": 1, "module":self.__module.name, "busMember":False, "bitIdx":None, "busName":None }))

		if not self.__ecocell.pins.has_key(eco_pinName):
		    new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		else:
		    new_pin = self.__ecocell.pins[eco_pinName]

		new_pin.connectPort(new_port)
        	new_port.setFanin(new_pin)
		logging.debug("create new output port %s in %s module" %(patch_hierName, self.__module.name))

            else:
        	self.__ecooutputs.append((eco_pinName, patch_obj))
		logging.debug("find OutputMaps eco cell pin %s %s" %(eco_pinName, patch_obj))


    def _buildUpEcoCell(self):
    	""" build up Eco Cell """

	submodname = self.__eco.keys()[0]
	name = 'ECO_' + submodname
	self.__module = self.mods[self.topMod]
	self.__ecocell = self.__module.new_cell({ "name" : name, "submodname": submodname })
	logging.debug("buildup ECO cell in %s cell %s %s" %(self.__module.name, submodname, self.__ecocell))

    def _linkConnectEcoCell(self):
    	""" link connect Eco Cell """

    def _findFanOuts(self, obj):
    	""" find obj FanOuts  """
	if isinstance(obj, PortIn.PortIn) or isinstance(obj, PortClk.PortClk):
	    return obj.fanout
	elif hasattr(obj.net, 'fanout'):
	    return obj.net.fanout
	return []

    def _findFanIns(self, obj):
    	""" find obj FanIns """
	if isinstance(obj, PortOut.PortOut):
	    return obj.fanin
	elif hasattr(obj.net, 'fanin'):
	    return obj.net.fanin
	return []


    def _updateInputs(self):
    	""" update ECO Inputs
    	1. find ECO Pin input to Org Netlist and buildup connection map table
    	2. when the connection map table is done, find it's fanout and check the iter fanout had exist in the output list
    	3. if the step2 is done. del the fanout link and create new pin to new fanout link
    	"""


	for (eco_pinName, inobj) in self.__ecoinputs:
	    delfouts = [ (inobj,fout) for fout in self._findFanOuts(inobj) if fout in [it[1] for it in self.__ecooutputs] ]

	    if len(delfouts) == 1:
	    	netport, pin = delfouts[0]
	    	netport.delFanout(pin)
	        new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
	        new_pin.connect(netport, netport)
		netport.addFanout(new_pin)
		self.__ecoinputs.remove((eco_pinName, inobj))
		logging.debug("create ECO cell %s new input pin %s, connect net/port %s" %(self.__ecocell.name, eco_pinName, netport.name))


	found = False
	for (eco_pinName, outobj) in self.__ecooutputs:
	    if not isinstance(outobj, Port.Port):
		if not found:
		    new_net = self.__module.new_net({ "name":"ECO_W%d" %(self.__ecoid), "width":1, "busMember":False,  "bitIdx":None, "busName":None })
		    self.__ecoid += 1
		    found = True

		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
	    	new_pin.connect(new_net, new_net)
	    	outobj.connect(new_net, new_net)
	    	new_net.addFanout(outobj)
	    	new_net.setFanin(new_pin)
	    	self.__ecooutputs.remove((eco_pinName, outobj))
	    	logging.debug("create ECO cell %s new output pin %s, connect net %s" %(self.__ecocell.name, eco_pinName, new_net.name))


    def _updateOutputs(self):
    	""" update ECO Outputs
    	1. find ECO Pin output to Org Netlist and buildup connection map table
    	2. when the connection map table is done, find it's fanout and check the iter fanout had exist in the output list
    	3. if the step2 is done. del the fanin link and create new pin to new fanin link
    	"""

	for (eco_pinName, outobj) in self.__ecooutputs:
	    delfins = [ (outobj,fin) for fin in self._findFanIns(outobj) if fin in [it[1] for it in self.__ecoinputs] ]

	    if len(delfins) == 1:
		netport, pin = delfins[0]
	    	netport.delFanin(pin)
		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		new_pin.connect(netport, netport)
		netport.setFanin(new_pin)
		self.__ecooutputs.remove((eco_pinName, outobj))
		logging.debug("create ECO cell %s new output pin %s connect net/port %s" %(self.__ecocell.name, eco_pinName, netport.name))

	for (eco_pinName, inobj) in self.__ecoinputs:
	    if not isinstance(inobj, Port.Port):
		new_net = self.__module.new_net({ "name":"ECO_W%d" %(self.__ecoid), "width":1, "busMember":False,  "bitIdx":None, "busName":None })
		self.__ecoid += 1
		inobj.connect(new_net, new_net)
		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		new_pin.connect(new_net, new_net)
		new_net.addFanout(new_pin)
		new_net.setFanin(inobj)
		self.__ecoinputs.remove((eco_pinName, inobj))
		logging.debug("create ECO cell %s new input pin %s, connect net %s" %(self.__ecocell.name, eco_pinName, new_net.name))


    def runECO(self):
    	""" only for one ECO cell can be inserted """

	self._buildUpEcoCell()

	self._findInputMaps()
	self._findOutPutMaps()

	self._updateInputs()
	self._updateOutputs()


    def update(self):
    	""" update cell module ports when the runECO is done """

    def report(self):
    	pass

################################################################################
################################################################################
if __name__ == "__main__":
    import doctest
    doctest.testmod()
