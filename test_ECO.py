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


    def _runECOCmpExp(self, **kwargs):
	""" run compare ECO and expect """

	eco = ECO.ECO()
	eco.readYAML( kwargs['CELLLIB'] )
	eco.readVerilog( kwargs['ORGVERILOG'] )
	eco.buildup( kwargs['TOPMODULE'] )
	eco.checkDesign()
	eco.readECO( kwargs['ECO'] )
	eco.runECO()
	eco.checkDesign()
	eco.writeVerilog( kwargs['ECOVERILOG'] )

	exp = Netlist.Netlist()
	exp.readYAML( kwargs['CELLLIB'] )
	exp.readVerilog( kwargs['EXPVERILOG'] )
	exp.buildup( kwargs['TOPMODULE'] )
	exp.checkDesign()
	exp.writeVerilog( 'align_' + kwargs['EXPVERILOG'] )

	test = Netlist.Netlist()
	test.readYAML( kwargs['CELLLIB'] )
	test.readVerilog( kwargs['ECOVERILOG'] )
	test.buildup( kwargs['TOPMODULE'] )
	test.checkDesign()
	test.writeVerilog( 'align_' + kwargs['ECOVERILOG'] )

	self.assertTrue(filecmp.cmp('align_' + kwargs['ECOVERILOG'], 'align_' + kwargs['EXPVERILOG']))

	os.system('rm -rf *.v *.yml')


    def test_module_INV_new_cell(self):
    	""" test moudle INV new cell  """

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
    I: ECO_in
  outputs:
    ZN: ECO_out
  primitive: not I
"""
	exptest = \
"""
module TOP( in, out );

    output [  1: 0 ] out;
    output ECO_out
    input  [  1: 0 ] in;
    input ECO_in

    INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
    INVD1 ECO_INVD1( .I( ECO_in ), .ZN( ECO_out ) );
endmodule
"""

	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')
	self._genTestExpList(exptest, 'exptest.v')

	self._runECOCmpExp(
		CELLLIB	    = 'test.yml',
		ORGVERILOG  = 'test.v',
		TOPMODULE   = 'TOP',
		ECO	    = 'etest.yml',
		ECOVERILOG  = 'ecotest.v',
		EXPVERILOG  = 'exptest.v',
	    )


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
	exptest = \
"""
module TOP( in, out );

    output [  1: 0 ] out;
    input  [  1: 0 ] in;

    wire ECO_W0;

    INVD1 ECO_INVD1( .I( in[0] ), .ZN( ECO_W0 ) );
    INVD1 U0( .I( ECO_W0 ), .ZN( out[0] ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
endmodule
"""

	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')
	self._genTestExpList(exptest, 'exptest.v')

	self._runECOCmpExp(
		CELLLIB	    = 'test.yml',
		ORGVERILOG  = 'test.v',
		TOPMODULE   = 'TOP',
		ECO	    = 'etest.yml',
		ECOVERILOG  = 'ecotest.v',
		EXPVERILOG  = 'exptest.v',
	    )


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
	exptest = \
"""
module TOP( in, out );

    output [  1: 0 ] out;
    input  [  1: 0 ] in;

    wire ECO_W0;

    INVD1 U0( .I( in[0] ), .ZN( ECO_W0 ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
    INVD1 ECO_INVD1( .I( ECO_W0 ), .ZN( out[0] ) );
endmodule
"""

	self._genTestNetList(vtest, 'test.v')
	self._genTestCellLib(ytest, 'test.yml')
	self._genTestECORule(etest, 'etest.yml')
	self._genTestExpList(exptest, 'exptest.v')

	self._runECOCmpExp(
		CELLLIB	    = 'test.yml',
		ORGVERILOG  = 'test.v',
		TOPMODULE   = 'TOP',
		ECO	    = 'etest.yml',
		ECOVERILOG  = 'ecotest.v',
		EXPVERILOG  = 'exptest.v',
	    )

def suite():
    tests = ['test_module_INV_input_to_cell', \
    	    'test_module_INV_cell_to_output',\
    	    'test_module_INV_new_cell',]
    return unittest.TestSuite(map(TestECO, tests))


if __name__=='__main__':
    unittest.main(defaultTest='suite')
#    unittest.main()
