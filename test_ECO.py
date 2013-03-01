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


    def test_eco_add_new_top_inoutport(self):
	""" test moudle add new inoutput port """

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
    Z:  new_out
  primitive: A1 and A2
"""

	exptest = \
"""
module TOP( new_in, new_out, in, out );

    output [  1: 0 ] out;
    input  [  1: 0 ] in;
    input new_in;
    output new_out;

    AN2D1 ECO_AN2D1( .A1( new_in ), .A2( in[0]), .Z( new_out ) );
    INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
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

	exptest = \
"""
module TOP( new_in, in, out );

    output [  1: 0 ] out;
    input  [  1: 0 ] in;
    input new_in;

    wire ECO_W0;

    AN2D1 ECO_AN2D1( .A1( new_in ), .A2( in[0]), .Z( ECO_W0 ) );
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

	exptest = \
"""
module TOP( in, out );

    output [  1: 0 ] out;
    input  [  1: 0 ] in;

    wire ECO_W0;

    INVD1 U0( .I( in[0] ), .ZN( ECO_W0 ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
    AN2D1 ECO_AN2D1( .A1( in[0] ), .A2( ECO_W0 ), .Z( out[0] ) );
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


    def test_eco_add_new_net_net(self):
	""" test adding new net to net """

	vtest = \
"""
module TOP( in, out );
input in;
output out;
wire W0;
INVD1 U0( .I( in ), .ZN( W0 ) );
INVD1 U1( .I( W0 ), .ZN( out ) );
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
    A1: eco_in
    A2: U0/ZN
  outputs:
    Z:  U1/I
  primitive: A1 and A2
"""

	exptest = \
"""
module TOP( eco_in, in, out );

    output  out;
    input   in;
    input   eco_in;

    wire ECO_W0;
    wire w0;

    INVD1 U0( .I( in ), .ZN( W0 ) );
    INVD1 U1( .I( ECO_W0 ), .ZN( out ) );
    AN2D1 ECO_AN2D1( .A1( eco_in ), .A2( W0 ), .Z( ECO_W0 ) );
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

    tests = [
    	#'test_eco_add_new_top_assign',
	'test_eco_add_new_top_inport',
	'test_eco_add_new_top_outport',
	'test_eco_add_new_top_inoutport',
    	#'test_eco_add_new_net_input',
    	#'test_eco_add_new_net_output',
    	'test_eco_add_new_net_net',
	]

    return unittest.TestSuite(map(TestECO, tests))


if __name__=='__main__':
    unittest.main(defaultTest='suite')
