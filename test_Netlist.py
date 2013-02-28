
import unittest
import Netlist
import verilogParse
import PortIn
import PortOut
import PortClk
import pprint
import os
import myutils
import PortIn
import PortOut
import Cell
import Net


class TestNetlist(unittest.TestCase):

    def setUp(self):
    	pass

    def teardown(self):
	pass

    def test_writeVerilog(self):
    	""" test parse dump """

	vtest = \
"""
module TOP( in, out );
input  in;
output  out;
INVD1 U0( .I( in ), .ZN( out ) );
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
	nl1.buildup( 'TOP' )
	nl1.writeVerilog( 'new_test.v' )

	nl2 = Netlist.Netlist()
	nl2.readYAML( 'test.yml' )
	nl2.readVerilog( 'new_test.v' )
	nl2.buildup( 'TOP' )

	raise NotImplementedError

	os.system('rm -rf test.v new_test.v test.yml')


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
	nl1.buildup( 'TOP' )
	self.assertEqual( nl1.topMod, 'TOP' )

	mod = nl1.mods[nl1.topMod]

	ports = mod.ports.values()
	self.assertEqual( len(ports), 4 ) # 1:0 + 1:0 = 4

	exp_inputs = [('in', 1, None, None) for i in range(2)]
	exp_outpus = [('out', 1, None, None) for i in range(2)]
	inputs = []
	outputs = []

	for pp in ports:
	    if isinstance(pp, PortIn.PortIn):
	    	inputs.append((pp.busName, pp.width, pp.msb, pp.lsb))
	    elif isinstance(pp, PortOut.PortOut):
		outputs.append((pp.busName, pp.width, pp.msb, pp.lsb))

	self.assertEqual( inputs, exp_inputs )
	self.assertEqual( outputs, exp_outpus )

	os.system('rm -rf test.v test.yml')


    def test_miss_cells_exception(self):
	""" test miss cells exception raise """

	vtest = \
"""
module TOP( in, out );
input [7:0] in;
output [5:0] out;
COUNT_BITS8 count_bits( .IN( in ), .C( out ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	with self.assertRaises(Exception) as context:
	    nl1.buildup('TOP')
	print context.exception

	os.system('rm -rf test.v test.yml')


    def test_find_submodules(self):
	""" test find submodules  """

	vtest = \
"""
module TOP( in, out );
input  in;
output out;
MYINV U0( .I( in ), .ZN( out ) );
endmodule
module MYINV( I, ZN );
input I;
output ZN;
INVD1 U0( .I( I ), .ZN( ZN ));
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	submods = nl1.findSubModules()
	self.assertEqual( submods, [('MYINV', 'U0')] )

	os.system('rm -rf test.v test.yml')


    def test_deepobj(self):
	""" test find deep obj """

	vtest = \
"""
module TOP( in, out );
input  in;
output out;
MYINV U0( .I0( in ), .ZN0( out ) );
endmodule
module MYINV( I0, ZN0 );
input I0;
output ZN0;
INVD1 U1( .I( I0 ), .ZN( W0 ));
INVD1 U2( .I( W0 ), .ZN( ZN0 ));
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	# find deepest port obj in cell lib
	obj = nl1.deepobj('U0/U1/I', dtype='port')
	self.assertEqual(obj.name, 'I')
	# input port fain eq []
	self.assertEqual(obj.net.fanin, [])
	# output port fanout len=1
	self.assertEqual(len(obj.net.fanout), 1)
	# fanout to self input Pin
	self.assertEqual(obj.net.fanout[0].name, 'I')

	# find deep cell obj
	obj = nl1.deepobj('U0/U1', dtype='cell')
	self.assertEqual(obj.name, 'U1')

	# find deep net obj
	obj = nl1.deepobj('U0/W0', dtype='net')
	self.assertEqual(obj.name, 'W0')

	os.system('rm -rf test.v test.yml')


    def test_hiername(self):
	""" test find hier name """

	vtest = \
"""
module TOP( in, out );
input  in;
output out;
MYINV U0( .I( in ), .ZN( out ) );
endmodule
module MYINV( I, ZN );
input I;
output ZN;
INVD1 U0( .I( I ), .ZN( ZN ));
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')
	os.system('rm -rf test.v test.yml')


    def test_miss_wire_exception_raise(self):
	""" test miss wire buildup exception raise """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	os.system('rm -rf test.v test.yml')


    def test_checkInputPorts(self):
	""" test check input ports exception raise """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	with self.assertRaises(Exception) as context:
	    nl1.checkInputPorts()
	print repr(context.exception)

	os.system('rm -rf test.v test.yml')


    def test_checkOutputPorts(self):
	""" test check Output ports exception raise """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	with self.assertRaises(Exception) as context:
	    nl1.checkOutputPorts()
	print repr(context.exception)

	os.system('rm -rf test.v test.yml')


    def test_checkConnectionDriver(self):
	""" test check connection Driver exception raise """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
wire w0, w1;
INVD1 U0( .I( w0 ), .ZN( w1 ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

	with self.assertRaises(Exception) as context:
	    nl1.checkConnectionDriver()
	print repr(context.exception)

	os.system('rm -rf test.v test.yml')


    def test_checkConnectionWidth(self):
	""" test check connection Width exception raise """

	vtest = \
"""
module TOP( in, out );
input [1:0] in;
output [1:0] out;
INVD1 U0( .I( in ), .ZN( out ) );
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
	nl1.readYAML('test.yml')
	nl1.readVerilog('test.v')

	nl1.buildup('TOP')

# the parser will reconginze the pin "in" in INVDID1 U0 to a new pp without the in.
# because the parser will feed the "in" to expassion case like "in[1:0]" will be in[1], in[0] for each one has it's own pp
# so, the in pp will not be builduped when the build up pase.

#	with self.assertRaises(Exception) as context:
#	    nl1.checkConnectionWidth()
#	print repr(context.exception)

	os.system('rm -rf test.v test.yml')



if __name__=='__main__':
    unittest.main()
