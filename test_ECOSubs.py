import unittest
import Netlist
import ECO
import os
import filecmp

class TestECO(unittest.TestCase):

    def setUp(self):
    	pass

    def teardown(self):
	pass

    def _genTestNetList(self, vtest, name='test.v'):
	""" gen test Netlist """
        VFH = open( name , 'w' )
        VFH.write( vtest )
        VFH.close()

    def _genTestCellLib(self, ytest, name='test.yml'):
    	""" gen test lib """
        YFH = open( name , 'w' )
        YFH.write( ytest )
        YFH.close()

    def _genTestECORule(self, etest, name='etest.yml'):
    	""" gen ECO rule """
        EFH = open( name , 'w' )
        EFH.write( etest )
        EFH.close()

    def _genTestExpList(self, exptest, name='exptest.v'):
    	""" gen exp Netlist to check when after runing ECO """
        EFH = open( name , 'w' )
        EFH.write( exptest )
        EFH.close()

    def test_eco_add_new_top_assign(self):
	""" test assign new 0/1 to internal cell pin connection """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
endmodule
"""
	ytest = \
"""
AN2D1:
  inputs:
    A1: 1
    A2: 1
  outputs:
    Z: 1
  primitive: A1 and A2

INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
AN2D1:
  inputs:
    A1: 0
    A2: in[0]
  outputs:
    Z:  U0/I
  primitive: A1 and A2
"""
	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')

	eco = ECO.ECO()
	eco.readYAML( 'test.yml' )
	eco.readVerilog( 'test.v' )
	eco.buildup( 'TOP' )
	eco.checkDesign()
	eco.readECO( 'etest.yml' )
	eco.runECO()
	eco.checkDesign()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1', 'AN2D1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_AN2D1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_AN2D1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['A1', 'A2', 'Z']))

	# check the new input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A1'].net.fanout), 1)
	self.assertEqual(cell.pins['A1'].net.fanout[0], cell.pins['A1'])

	# check the org input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A2'].port.fanout), 1)
	self.assertEqual(cell.pins['A2'].port.fanout[0], cell.pins['A2'])

	# check the new output pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['Z'].net.fanout), 1)
	self.assertEqual(cell.pins['Z'].net.fanout[0], eco.mods['TOP'].cells['U0'].pins['I'])

	# check the new output pin has only one fanin for it's self
	self.assertEqual(len(cell.pins['Z'].net.fanin), 1)
	self.assertEqual(cell.pins['Z'].net.fanin[0], cell.pins['Z'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted([0, 'ECO_W0']))


    def test_eco_add_new_top_inport(self):
    	""" test adding new input port to top module """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
endmodule
"""
	ytest = \
"""
AN2D1:
  inputs:
    A1: 1
    A2: 1
  outputs:
    Z: 1
  primitive: A1 and A2

INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
AN2D1:
  inputs:
    A1: new_in
    A2: in[0]
  outputs:
    Z:  U0/I
  primitive: A1 and A2
"""
	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')

	eco = ECO.ECO()
	eco.readYAML( 'test.yml' )
	eco.readVerilog( 'test.v' )
	eco.buildup( 'TOP' )
	eco.checkDesign()
	eco.readECO( 'etest.yml' )
	eco.runECO()
	eco.checkDesign()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1', 'AN2D1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_AN2D1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_AN2D1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['A1', 'A2', 'Z']))

	# check the new input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A1'].port.fanout), 1)
	self.assertEqual(cell.pins['A1'].port.fanout[0], cell.pins['A1'])

	# check the org input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A2'].port.fanout), 1)
	self.assertEqual(cell.pins['A2'].port.fanout[0], cell.pins['A2'])

	# check the new output pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['Z'].net.fanout), 1)
	self.assertEqual(cell.pins['Z'].net.fanout[0], eco.mods['TOP'].cells['U0'].pins['I'])

	# check the new output pin has only one fanin for it's self
	self.assertEqual(len(cell.pins['Z'].net.fanin), 1)
	self.assertEqual(cell.pins['Z'].net.fanin[0], cell.pins['Z'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['new_in', 'in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted(['ECO_W0']))


    def test_eco_add_new_top_outport(self):
    	""" test adding new output port to top module """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
endmodule
"""
	ytest = \
"""
AN2D1:
  inputs:
    A1: 1
    A2: 1
  outputs:
    Z: 1
  primitive: A1 and A2

INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
AN2D1:
  inputs:
    A1: in[0]
    A2: U0/ZN
  outputs:
    Z:  out[0]
  primitive: A1 and A2
"""
	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')

	eco = ECO.ECO()
	eco.readYAML( 'test.yml' )
	eco.readVerilog( 'test.v' )
	eco.buildup( 'TOP' )
	eco.checkDesign()
	eco.readECO( 'etest.yml' )
	eco.runECO()
	eco.checkDesign()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1', 'AN2D1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_AN2D1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_AN2D1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['A1', 'A2', 'Z']))

	# check the new input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A1'].port.fanout), 2)
	self.assertEqual(sorted(cell.pins['A1'].port.fanout), sorted([cell.pins['A1'], eco.mods['TOP'].cells['U0'].pins['I']]))

	# check the org input pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['A2'].net.fanout), 1)
	self.assertEqual(cell.pins['A2'].net.fanout[0], cell.pins['A2'])

	# check the org input pin has only one fanin for it's self
	self.assertEqual(len(cell.pins['A2'].net.fanin), 1)
	self.assertEqual(cell.pins['A2'].net.fanin[0], eco.mods['TOP'].cells['U0'].pins['ZN'])

	# check the new output pin has only one fanin for it's self
	self.assertEqual(len(cell.pins['Z'].port.fanin), 1)
	self.assertEqual(cell.pins['Z'].port.fanin[0], cell.pins['Z'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted(['ECO_W0']))


    def test_eco_add_new_top_inoutport(self):
    	""" test adding new in/output port to top module """
    	pass

    def test_eco_add_new_net_input(self):
    	""" test adding new net to input """
    	pass

    def test_eco_add_new_net_output(self):
    	""" test adding new net to output """
    	pass

    def test_eco_add_new_net_net(self):
    	""" test adding new net to net """
    	pass


def suite():
    tests = [
    	'test_eco_add_new_top_assign',
	'test_eco_add_new_top_inport',
	'test_eco_add_new_top_outport',
	'test_eco_add_new_top_inoutport',
    	'test_eco_add_new_net_input',
    	'test_eco_add_new_net_output',
    	'test_eco_add_new_net_net',
	]

    return unittest.TestSuite(map(TestECO, tests))


if __name__=='__main__':
    unittest.main(defaultTest='suite')

