#!/usr/bin/python

import Module
import PortIn
import PortOut
import PortClk
import Net
import Pin
import Port
import Cell
import ConfigParser
from ordereddict import OrderedDict
import os
import yaml
import pickle
import re
import verilogParse
import myutils
from collections import defaultdict
################################################################################
################################################################################
class Netlist(object):
    """
    This class is a Python datastructure for storing/querying Verilog
    netlists.

    The Netlist module is able to read both from Verilog files and special
    YAML-formatted files. The YAML format is currently much faster. I have
    a separate Verilog-->YAML converter that I've used to create YAML files up
    until now (based in Perl, booo). The Verilog support in Python is newly
    added.

    This example shows how to read and link netlists. It demonstrates both
    reading from Verilog (n1) and YAML (n2), and then verifies that
    the a few of the netlist properties match.

    >>> nl1 = Netlist()
    >>> nl1.readYAML("test.yml")
    >>> nl1.readVerilog("test/top.gv")
    >>> nl1.buildup("TOP")
    >>> nl1.topMod
    'TOP'
    >>> mod1 = nl1.mods[nl1.topMod]
    >>> nl1.checkDesign()
    """

    mods = property(lambda self: self.__mods)
    yaml = property(lambda self: self.__yaml)
    topMod = property(lambda self: self.__topMod)

    def __init__(self):
        self.__mods = {}
        self.__topMod = None
        self.__yaml = {}
	self.__modstack =[]


    def link(self, topModule):
	self.__topMod = topModule


    def buildup(self, topModule):
        " buildup the design together"
        if topModule not in self.__mods:
            raise Exception(str("buildup error, " + topModule +
                                " has not been defined"))

        mod = self.__mods[topModule]

        missing = set()
        # check all cells
        for cell in mod.cells:
            if mod.cells[cell].submodname not in self.__mods:
                missing.add(mod.cells[cell].submodname)

        if len(missing) > 0:
            raise Exception(str("buildup error, " +
                                str(missing) +
                                " have not been defined"))

        for cell in mod.cells:
            submod = self.__mods[mod.cells[cell].submodname]
            mod.cells[cell].linkMod(submod)
            for pin in mod.cells[cell].pins:
                if pin not in submod.ports:
                    raise Exception(str("port " + pin + " not in "
                                        + submod.name))
                mod.cells[cell].pins[pin].connectPort(submod.ports[pin])
                net =  mod.cells[cell].pins[pin].net
                if submod.ports[pin].direction == "in":
                    net.addFanout(mod.cells[cell].pins[pin])
                else:
                    net.setFanin(mod.cells[cell].pins[pin])

        self.__modstack.append(topModule)
	self.__topMod = topModule

	for submm, subcell in self.findSubModules():
	    # set module hier(top/sub) link and it's unique name
            top_mod = self.__mods[self.__topMod]
	    sub_mod = self.__mods[submm]

	    self.buildup(submm)
	    self.__modstack.pop(-1)

        self.__topMod = self.__modstack[0]


    def findSubModules(self):
	""" if the cur module has sub modules(cell) then return it """
        submodules = []
        mod = self.__mods[self.__topMod]

        # check all cells
        for cell in mod.cells:
            if mod.cells[cell].submodname not in self.__yaml.keys():
                submodules.append((mod.cells[cell].submodname, cell))
	return submodules


    def checkInputPorts(self):
    	""" make sure input ports ONLY connect to input ports """

	# check top module input port Fanin is empty, Fanout port is Not empty
	for port_nm, port_pp in self.__mods[self.__topMod].ports.items():
	    if isinstance(port_pp, PortIn.PortIn) and port_pp.direction == 'in':

		if isinstance(port_pp.fanin, list) and len(port_pp.fanin) > 0:
		    raise Exception(str("the input port %s Fanin in top module %s is not empty [%s]" \
		    	    %(port_nm, \
		    	    self.__topMod,
		    	    ",".join([i.portname for i in port_pp.fanin]))))

		if isinstance(port_pp.fanout, list) and len(port_pp.fanout) == 0:
		    raise Exception(str("the input port %s Fanout in top module %s is empty" \
		    	    %(port_nm, self.__topMod)))

		# check top module input port Fanout should be link to the Basic Cell or sub module input
		missing = []
		for pp in port_pp.fanout:
		    if not isinstance(pp.port, (PortIn.PortIn, PortClk.PortClk)):
		    	missing.append(pp.portname)

		if len(missing) > 0:
		    raise Exception(str("the input port %s Fanout should be input type [%s]" \
		    	    %(port_nm, ",".join(missing))))


    def checkOutputPorts(self):
	""" make sure output ports ONLY connect to output ports """

	# check top module output Fanout is Not empty, Fanin is empty
	for port_nm, port_pp in self.__mods[self.__topMod].ports.items():

	    if isinstance(port_pp, PortOut.PortOut) and port_pp.direction == 'out':

		if isinstance(port_pp.fanin, list) and len(port_pp.fanin) == 0:
		    raise Exception(str("the output port %s Fanin in top module %s is empty" \
		    	    %(port_nm, self.__topMod)))

#		if port_pp.fanout != None and len(port_pp.fanout) > 0:
#		    raise Exception(str("the output port %s Fanout in top module %s is not empty [%s]"\
#		    	    %(port_nm, \
#		    	    self.__topMod, \
#			    ",".join([i.portname for i in port_pp.fanout]))))


    def checkConnectionWidth(self):
    	""" check all connection width """

	raise NotImplementedError, """
# the parser will reconginze the pin "in" in INVDID1 U0 to a new pp without the in.
# because the parser will feed the "in" to expassion case like "in[1:0]" will be in[1], in[0] for each one has it's own pp
# so, the in pp will not be linked when the build up pase.
"""

        mod = self.__mods[self.__topMod]
	missing = []

        for cell in mod.cells:
            submod = self.__mods[mod.cells[cell].submodname]
            mod.cells[cell].linkMod(submod)

            for pin in mod.cells[cell].pins:
            	pp  = mod.cells[cell].pins[pin]
                net = mod.cells[cell].pins[pin].net

		if isinstance(pp.port, PortOut.PortOut):
		    for fout in net.fanout:
		    	if fout.port.width != pp.port.width:
		    	    missing.append("%s.%s(%d) != %s.%s(%d)" \
		    	    	    %(cell, \
		    	    	    pp.portname, \
		    	    	    pp.port.width, \
		    	    	    fout.cell.submodname, \
		    	    	    fout.portname, \
		    	    	    fout.port.width))

		if isinstance(pp.port, PortIn.PortIn) or isinstance(pp.port, PortClk.PortClk):
		    for fin in net.fanin:
			if fin.port.width != pp.port.width:
			    missing.append("%s.%s(%d) != %s.%s(%d)" \
			    	    %(cell, \
			    	    pp.portname, \
			    	    pp.port.width, \
			    	    fin.cell.submodname, \
			    	    fin.portname, \
			    	    fin.port.width))

		if len(missing) > 0:
		    raise Exception(str("\n".join(missing)))


    def checkConnectionDriver(self):
	""" check connection Driver has exist """

        mod = self.__mods[self.__topMod]

        missing_fout = defaultdict(list)
	missing_fin  = defaultdict(list)

	top_ports = self.__mods[self.__topMod].ports.keys()

        for cell in mod.cells:
            submod = self.__mods[mod.cells[cell].submodname]
            mod.cells[cell].linkMod(submod)

            for pin in mod.cells[cell].pins:
            	pp  = mod.cells[cell].pins[pin]
                net = mod.cells[cell].pins[pin].net

		if isinstance(pp.port, PortOut.PortOut):
		    # the cur cell port is connect to top module ports or not
		    if len(net.fanout) == 0:
			if pp.netname not in top_ports:
			    missing_fout[cell].append('(' + pp.portname + ',' + pp.netname + ')')

		    # if fanout is connected to the internal cells
		    for fout in net.fanout:
			if fout.portname == None:
			    if fout.netname not in top_ports:
			    	missing_fout[cell].append('(' + pp.portname + ',' + pp.netname + ')')

		if isinstance(pp.port, PortIn.PortIn) or isinstance(pp.port, PortClk.PortClk):
		    # the cur cell port is connect to top module ports or not
		    if len(net.fanin) == 0:
			if pp.netname not in top_ports:
			   missing_fin[cell].append('(' + pp.portname + ',' + pp.netname + ')')

		    # if fanin is connected to the internal cells
		    for fin in net.fanin:
			if fin.portname == None:
			    if fin.netname not in top_ports:
				missing_fin[cell].append('(' + pp.portname + ',' + pp.netname + ')')

	if missing_fin or missing_fout:
	    missing = []
	    for cc, fin in missing_fin.items():
	    	missing.append(cc + ' missing fanin ' + ','.join(fin))
	    for cc, fout in missing_fout.items():
	    	missing.append(cc + ' missing_fout ' + ','.join(fout))

	    raise Exception(str("\n".join(missing)))


    def checkDesign(self):
        "verify the design has legal connections (post-linking)"

        self.checkInputPorts()
        self.checkOutputPorts()
	self.checkConnectionDriver()
	#self.checkConnectionWidth()


    def hiername(self, obj, names=[]):
	raise NotImplementedError, """
# we only support top to down search, because the mod could have the different uniqu cell name,
such as INV1 U0(); ... INV1 U1();.. . cell U0, U1 have the same mod,
in current design, we only record module one time in the same share link
"""


    def deepobj(self, name, dtype=None):
	""" get deep object from hier name """

	if dtype not in ['pin', 'port', 'cell', 'net']:
	    raise Exception("deepobj not suppoty dtype(%s) [pin, port, cell, net]" %(dtype))

	names = str(name).split('/')
	mod = self.__mods[self.__topMod]
	cur_cell = None

	while names:
	    name = names.pop(0)

	    if len(names) == 0:
		if dtype in ['port', 'pin']:
		    # check it's port or cell, if it's in top module return port else return pin
		    if cur_cell:
			return None if name not in cur_cell.pins else cur_cell.pins[name]
		    else:
		    	return None if name not in mod.ports else mod.ports[name]
		elif dtype == 'cell':
		    return None if name not in mod.cells else mod.cells[name]
		elif dtype == 'net':
		    return None if name not in mod.nets else mod.nets[name]
		else:
		    raise Exception("deepobj foun %s, %s [port,cell,net] error" %(name, dtype))
	    else:
	        # check all cells
	        found = False
	        for cell in mod.cells:
		    if cell == name:
		    	cur_cell = mod.cells[cell]
			mod = mod.cells[cell].submod
			found = True
		if not found:
		    return None


    def addModule(self, mod):
        modname = mod.name
        if modname in self.__mods:
            print "Warning: " + modname + " has been multiply defined"
        self.__mods[modname] = mod

    def readVerilog(self, verilogFile):
        """ Parse a Gate-level Verilog file using Python"""
        mods = verilogParse.parseFile(verilogFile)
	for mod in mods:
	    self.__mods[mod.name] = mod

    def writeVerilog(self, vFileName):
        """ Write a gate-level verilog file """

        tm = self.mods[ self.topMod ]
        lines = []

        # -- ?? -- "busMember":False, "bitIdx":None,   "busName":None    })

        # declare the module
        ports = set()
        minBit = {}
        maxBit = {}
        for p in sorted(tm.ports.values()):
            if p.busMember:
                ports.add( ( p.busName, p.direction ) )
                if p.busName in minBit:
                    l = minBit[ p.busName ]
                    r = maxBit[ p.busName ]
                    assert p.bitIdx != l
                    assert p.bitIdx != r
                    if p.bitIdx < l: minBit[ p.busName ] = p.bitIdx
                    if p.bitIdx > r: maxBit[ p.busName ] = p.bitIdx
                else:
                    minBit[ p.busName ] = p.bitIdx
                    maxBit[ p.busName ] = p.bitIdx
            else:
                ports.add( ( p.name, p.direction ) )
        portsCsv = ', '.join( [ x[0] for x in list( ports ) ] )
        lines.append( 'module %s( %s );' % ( self.topMod, portsCsv ) )
        lines.append( '' )

        # declare i/o ports
        for ( portName, dirxn ) in sorted(ports):
            if portName in minBit:
                assert minBit[ portName ] == 0
                l = minBit[ portName ]
                r = maxBit[ portName ]
                if   dirxn == 'in':  lines.append( '    input  [ %2d:%2d ] %s;' % ( r, l, portName ))
                elif dirxn == 'out': lines.append( '    output [ %2d:%2d ] %s;' % ( r, l, portName ))
            else:
                if   dirxn == 'in':  lines.append( '    input  %s;' % ( portName ))
                elif dirxn == 'out': lines.append( '    output %s;' % ( portName ))
                else: assert False
        lines.append( '' )

        # declare the wires
        minBit = {}
        maxBit = {}
        nets = set()
        for n in sorted(tm.nets.values()):
              if n.busMember:
                  nets.add( n.busName )
                  if n.busName in minBit:
                      l = minBit[ n.busName ]
                      r = maxBit[ n.busName ]
                      print type(n.bitIdx)
                      print type(l)
                      print '----'
                      assert int( n.bitIdx ) != l
                      assert int( n.bitIdx ) != r
                      if int( n.bitIdx ) < l: minBit[ n.busName ] = int ( n.bitIdx )
                      if int( n.bitIdx ) > r: maxBit[ n.busName ] = int ( n.bitIdx )
                  else:
                      minBit[ n.busName ] = int( n.bitIdx )
                      maxBit[ n.busName ] = int( n.bitIdx )
              else:
                  nets.add( n.name )

        for netName in sorted(nets):
            if netName in minBit:
                #assert minBit[ netName ] == 0
                l = minBit[ netName ]
                r = maxBit[ netName ]
                lines.append( '    wire [ %2d:%2d ] %s;' % ( r, l, netName ) )
            else:
                lines.append( '    wire %s;' % ( netName ))
        lines.append( '' )

        # instantiate the cells
	for c in sorted(tm.cells.values(), key=lambda k: k.name):
            ports = []
	    for p in sorted(c.pins.values(), key=lambda k: k.name):
                ports.append( '.%s( %s )' % ( p.name, p.net.name ))
            ports = ', '.join( ports )
            lines.append( '    %s %s( %s );' % ( c.submodname, c.name, ports ))
        lines.append( 'endmodule' )
        VFH = open( vFileName, 'w' )
        for line in lines:
            VFH.write( line + '\n' )
        VFH.close()

    def dumpPickle(self, piklFile):
        " Dump self to a pickle file"

        FH = open( piklFile, 'w' )
        pickle.dump( self, FH )
        FH.close()

    def readYAML(self, yamlFile):
        " Read a YAML config file, build a netlist"

        file = open(yamlFile)
        nl = yaml.safe_load(file)
        file.close()

        # save the config info in case we need it later
        self.__yaml.update(nl)

        for modname in nl.keys():
            mod = Module.Module({"name":modname})

            inputs = myutils.cleanget(nl.get(modname), "inputs")
            for name in inputs:
                #todo: add parsing code to determine width msb/lsb here
                width = int(inputs.get(name))
                tuples = self.__makePortTupleList__(name, width)
                for ( name, width, isBusMember, bitIdx, busName ) in tuples:
                    mod.add_port(PortIn.PortIn({ "name":name, "width":width, "module":mod, "busMember":isBusMember, "bitIdx":bitIdx, "busName":busName }))

            outputs = myutils.cleanget(nl.get(modname), "outputs")
            for name in outputs:
                #todo: add parsing code to determine width msb/lsb here
                width = int(outputs.get(name))
                tuples = self.__makePortTupleList__(name, width)
                for ( name, width, isBusMember, bitIdx, busName ) in tuples:
                    mod.add_port(PortOut.PortOut({ "name":name, "width":width, "module":mod, "busMember":isBusMember, "bitIdx":bitIdx, "busName":busName } ))

            clocks = myutils.cleanget(nl.get(modname), "clocks")
            for name in clocks:
                mod.add_port(PortClk.PortClk({"name":name, "module":mod, "busMember":False, "bitIdx":None, "busName":None }))

            cells = myutils.cleanget(nl.get(modname), "cells")
            for name in cells:
                submodname = cells.get(name)
                mod.new_cell({"name":name, "submodname":submodname})

            conns = myutils.cleanget(nl.get(modname), "connections")
            for name in conns:
                ports = conns.get(name)
                if name in mod.ports:
                    net = mod.ports.get(name)
                else:
                    #todo: add parsing code to determine width msb/lsb here
                    net = mod.new_net({"name":name, "width":1,
                                       "busMember": False,
                                       "bitIdx": None,
                                       "busName": None})
                for conn in ports.split():
                    cellport = conn.split('.')
                    if len(cellport) != 2:
                        raise Exception("Bad port: " + conn)
                    cell  = mod.cells.get(cellport[0])
                    pname = cellport[1]
                    pin = cell.new_pin({"name":pname, "portname":pname})
                    pin.connectNet(net)

            if modname in self.__mods:
                print "Warning: " + modname + " has been multiply defined"

            self.__mods[mod.name] = mod

    def __makePortTupleList__(self, name, width):
        tuples = []

        if width == 1:
            tuples.append((name, width, False, None, None ))
        elif width > 1:
            for i in range(0,width):
                tuples.append((name + "[" + str(i) + "]", 1, True, i, name ))
        else:
            raise Exception("Bad width parameter: " + width)

        return tuples


################################################################################
################################################################################
if __name__ == "__main__":
    import doctest
    doctest.testmod()
