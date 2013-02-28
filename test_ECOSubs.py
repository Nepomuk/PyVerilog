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


    def test_findInputMaps_new_net_assign(self):
	""" test findInputMaps assign new 0/1 to internal cell pin connection """

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
INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
INVD1:
  inputs:
    I: 0
  outputs:
    ZN: U0/I
  primitive: not I
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
	eco._buildUpEcoCell()
	eco._findInputMaps()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_INVD1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_INVD1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['I']))

	self.assertEqual(len(cell.pins['I'].net.fanout), 1)
	# check the new pin has only one fanout for it's self
	self.assertEqual(cell.pins['I'].net.fanout[0], cell.pins['I'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted([0]))


    def test_findInputMaps_new_top_port(self):
    	""" test findInputMaps create top module new input port """

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
INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
INVD1:
  inputs:
    I: new_in
  outputs:
    ZN: U0/I
  primitive: not I
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
	eco._buildUpEcoCell()
	eco._findInputMaps()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_INVD1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_INVD1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['I']))

	self.assertEqual(len(cell.pins['I'].port.fanout), 1)
	# check the new pin has only one fanout for it's self
	self.assertEqual(cell.pins['I'].port.fanout[0], cell.pins['I'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['new_in', 'in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted([]))


    def test_module_INV_input_to_cell(self):
    	""" test moudle INV input to cell """

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
INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
INVD1:
  inputs:
    I: in[0]
  outputs:
    ZN: U0/I
  primitive: not I
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

	eco._buildUpEcoCell()
	eco._findInputMaps()
	eco._findOutPutMaps()

	eco._updateInputs()
	eco.checkDesign()

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_INVD1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_INVD1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['I', 'ZN']))

	self.assertEqual(len(cell.pins['I'].port.fanout), 1)
	# check the new pin has only one fanout for it's self
	self.assertEqual(cell.pins['I'].port.fanout[0], cell.pins['I'])

	self.assertEqual(len(cell.pins['ZN'].net.fanout), 1)
	self.assertEqual(len(cell.pins['ZN'].net.fanin), 1)
	# check the new pin has only one fanout/fanin
	self.assertEqual(cell.pins['ZN'].net.fanin[0], cell.pins['ZN'])
	self.assertEqual(cell.pins['ZN'].net.fanout[0], eco.mods['TOP'].cells['U0'].pins['I'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted(['ECO_W0']))

	os.system('rm -rf *.yml *.v')


    def test_module_INV_cell_to_output(self):
    	""" test moudle INV cell to output """

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
INVD1:
  inputs:
    I: 1
  outputs:
    ZN: 1
  primitive: not I
"""
	etest = \
"""
INVD1:
  inputs:
    I: U0/ZN
  outputs:
    ZN: out[0]
  primitive: not I
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
	eco.writeVerilog( 'new_test.v' )

	# check mods map table
	self.assertEqual(sorted(eco.mods.keys()), sorted(['TOP', 'INVD1']))
	# check the new cell can be created
	self.assertEqual(sorted(eco.mods['TOP'].cells.keys()), sorted(['ECO_INVD1', 'U0', 'U1']))
	# pp to new cell
	cell = eco.mods['TOP'].cells['ECO_INVD1']
	# check the new cell has the new pin when the new assign set up
	self.assertEqual(sorted(cell.pins.keys()), sorted(['I', 'ZN']))

	# check the new pin has only one fanout for it's self
	self.assertEqual(len(cell.pins['I'].net.fanout), 1)
	self.assertEqual(cell.pins['I'].net.fanout[0], cell.pins['I'])

	# check the new pin has only one fanin for org net
	self.assertEqual(len(cell.pins['I'].net.fanin), 1)
	self.assertEqual(cell.pins['I'].net.fanin[0], eco.mods['TOP'].cells['U0'].pins['ZN'])

	# check the new pin has only one fanin
	self.assertEqual(len(cell.pins['ZN'].port.fanin), 1)
	self.assertEqual(cell.pins['ZN'].port.fanin[0], cell.pins['ZN'])

	# check the ports in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].ports), sorted(['in[0]', 'in[1]', 'out[0]', 'out[1]']))

	# check the nets in Top Module
	self.assertEqual(sorted(eco.mods['TOP'].nets), sorted(['ECO_W0']))


def suite():
    tests = ['test_module_INV_cell_to_output',]
    return unittest.TestSuite(map(TestECO, tests))


if __name__=='__main__':
    unittest.main(defaultTest='suite')
    #unittest.main()

    #suite = unittest.TestLoader().loadTestsFromTestCase(TestECO)
    #unittest.TestSuite(suite())
