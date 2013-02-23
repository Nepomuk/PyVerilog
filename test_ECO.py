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

    def test_module_1D_inoutput_msb_lsb(self):
    	""" test moudle 1D ECO INV """

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
    ZN: in[0]
  primitive: not I
"""
	exptest = \
"""
module TOP( in, out );

    output out;
    input  [  1: 0 ] in;

    wire ECO_0;

    INVD1 ECO_INVD1( .I( in[0] ), .ZN( ECO_0 ) );
    INVD1 U0( .I( ECO_0 ), .ZN( out[0] ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
endmodule
"""

        VFH = open( 'test.v' , 'w' )
        VFH.write( vtest )
        VFH.close()

        YFH = open( 'test.yml' , 'w' )
        YFH.write( ytest )
        YFH.close()

        EFH = open( 'etest.yml' , 'w' )
        EFH.write( etest )
        EFH.close()

        EFH = open( 'exptest.v' , 'w' )
        EFH.write( exptest )
        EFH.close()

	eco = ECO.ECO()
	eco.readYAML( 'test.yml' )
	eco.readVerilog( 'test.v' )
	eco.link( 'TOP' )
	eco.checkDesign()
	eco.readECO( 'etest.yml' )
	eco.runECO()
	eco.checkDesign()
	eco.writeVerilog( 'new_test.v' )

	print filecmp.cmp('new_test.v', 'exptest.v')

	#os.system('rm -rf test.v test.yml etest.yml new_test.v exptest.v')


if __name__=='__main__':
    unittest.main()
