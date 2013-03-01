
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
		    new_pin.connect(ass_net, ass_net) #???
		    ass_net.addFanout(new_pin)
		    logging.debug("create new net %s in %s module" %(patch_hierName, self.__module.name))
		else:
		    new_port = self.__module.add_port(PortIn.PortIn({ "name": patch_hierName, "width": 1, "module":self.__module, "busMember":False, "bitIdx":None, "busName":None }))
		    new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		    new_pin.connect(new_port, new_port) #?? new_pin.connectPort
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
		# multi drive outputs???
		new_port = self.__module.add_port(PortOut.PortOut({ "name": patch_hierName, "width": 1, "module":self.__module, "busMember":False, "bitIdx":None, "busName":None }))

		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})

		new_pin.connect(new_port, new_port)
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
	pass

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


    def _updateInputsFanout(self):
    	""" update ECO Inputs Fanout
    	1. find ECO Pin input from Org Netlist and buildup it's connection map<pinName, pinobj> table
    	2. if step1 is done, find it's fanout and check the iter fanout had exist in the output list
    	3. if step2 is done. del the fanout link which is connected to the same output pp and update to new net/port,
    	otherwise, create new pin to org fanout
    	"""

	precheck = []
	ecooutputs = [it[1] for it in self.__ecooutputs]

	for (eco_pinName, inobj) in self.__ecoinputs:
	    delfouts = [ (inobj,fout) for fout in self._findFanOuts(inobj) if fout in ecooutputs ]

	    if len(delfouts) == 1:
	    	inobj, pin = delfouts[0]
		netport = inobj if isinstance(inobj, Port.Port) else inobj.net
	    	netport.delFanout(pin)
	        new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		new_pin.connect(netport, netport)
		netport.addFanout(new_pin)
		precheck.append(pin)
		self.__ecoinputs.remove((eco_pinName, inobj))
		logging.debug("create ECO cell %s, new input pin %s, del fanout, connect net/port %s" %(self.__ecocell.name, eco_pinName, netport.name))

	    elif len(delfouts) == 0:
		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
	        new_pin.connect(inobj, inobj)
		netport = inobj if isinstance(inobj, Port.Port) else inobj.net
		netport.addFanout(new_pin)

	    else:
	    	raise Exception("")

	found = False
	for (eco_pinName, outobj) in self.__ecooutputs:
	    if outobj in precheck:
		if not isinstance(outobj, Port.Port): # bug when the output has two type one is net another is port???
		    if not found: # only one output and set it's fanin fanout
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


    def _updateOutputsFanin(self):
    	""" update ECO Outputs Fanin
    	1. find ECO Pin output from Org Netlist and buildup it's connection map table
    	2. if step1 is done, find it's fanout and check the iter fanout had exist in the input list
    	3. if step2 is done. del the fanout link which is connected to the same output pp and update to new net/port,
    	"""

	precheck = []
	ecoinputs = [it[1] for it in self.__ecoinputs]

	for (eco_pinName, outobj) in self.__ecooutputs:
	    delfins = [ (outobj,fin) for fin in self._findFanIns(outobj) if fin in ecoinputs ]

	    if len(delfins) == 1:
		outobj, pin = delfins[0]
		netport = outobj if isinstance(outobj, Port.Port) else outobj.net
	    	netport.delFanin(pin)
		new_pin = self.__ecocell.new_pin({"name":eco_pinName, "portname":eco_pinName})
		new_pin.connect(netport, netport)
		netport.setFanin(new_pin)
		precheck.append(pin)
		self.__ecooutputs.remove((eco_pinName, outobj))
		logging.debug("create ECO cell %s new output pin %s connect net/port %s" %(self.__ecocell.name, eco_pinName, netport.name))


	for (eco_pinName, inobj) in self.__ecoinputs:
	    if inobj in precheck:
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

	self._updateInputsFanout()
	self._updateOutputsFanin()

	self._inspect()

    def _rmUnLinkPorts():
    	""" remove unlinkable ports """

    def _rmUnLinkModules():
    	""" remove unlinkable modules """

    def _rmUnLinkCells():
    	""" remove unlinkable cells """

    def _rmUnLinkNets():
    	""" remove unlinkalbe nets """

    def _rmUnLinkPins():
    	""" remove unlinkalbe pins """

    def _rmUnLinkFanin():
    	""" remove unlinkalbe fanin """

    def _rmUnLinkFanout():
    	""" remove unlinkalbe fanout """

    def _inspect(self):
    	""" inspect cells, modules, ports when the runECO is done """

	self._rmUnLinkModules()
	self._rmUnLinkPorts()
	self._rmUnLinkCells()
	self._rmUnLinkNets()
	self._rmUnLinkPins()
	self._rmUnLinkFanout()
	self._rmUnLinkFanin()

    def report(self):
    	pass

################################################################################
################################################################################
if __name__ == "__main__":
    import doctest
    doctest.testmod()
