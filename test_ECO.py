import unittest
import Netlist
import ECO
import os

class TestECO(unittest.TestCase):

    def setUp(self):
    	pass

    def teardown(self):
	pass

    def test_module_1D_inoutput_msb_lsb(self):
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

        VFH = open( 'test.v' , 'w' )
        VFH.write( vtest )
        VFH.close()

        YFH = open( 'test.yml' , 'w' )
        YFH.write( ytest )
        YFH.close()

	nl1 = Netlist.Netlist()
	nl1.readYAML( 'test.yml' )
	nl1.readVerilog( 'test.v' )
	nl1.link( 'TOP' )
	self.assertEqual( nl1.topMod, 'TOP' )

	mod = nl1.mods[nl1.topMod]

	os.system('rm -rf test.v test.yml')


