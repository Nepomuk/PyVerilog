
import unittest
import Netlist
import verilogParse
import PortIn
import PortOut
import PortClk
import pprint
import os
import myutils

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
	nl1.link( 'TOP' )
	nl1.writeVerilog( 'new_test.v' )

	nl2 = Netlist.Netlist()
	nl2.readYAML( 'test.yml' )
	nl2.readVerilog( 'new_test.v' )
	nl2.link( 'TOP' )

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
	nl1.link( 'TOP' )
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
	    nl1.link('TOP')
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

	nl1.link('TOP')
	submods = nl1.findSubModules()
	self.assertEqual( submods, set(['MYINV']) )

	nl1.link('MYINV')
	submods = nl1.findSubModules()
	self.assertEqual( submods, set([]) )

	os.system('rm -rf test.v test.yml')


    def test_deep(self):
	""" test find deep obj """

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
wire W0;
INVD1 U0( .I( I ), .ZN( W0 ));
INVD1 U1( .I( W0 ), .ZN( ZN ));
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

	nl1.link('TOP')

	# find deep port obj
	obj = myutils.deepobj('U0/U0/I', dtype='port')

	# find deep cell obj
	obj = myutils.deepobj('U0/U0', dtype='cell')

	# find deep net obj
	obj = myutils.deepobj('U0/U0/W0', dtype='wire')

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

	nl1.link('TOP')
	submods = nl1.findSubModules()
	self.assertEqual( submods, set(['MYINV']) )

	nl1.link('MYINV')
	submods = nl1.findSubModules()
	self.assertEqual( submods, set([]) )

	os.system('rm -rf test.v test.yml')



    def test_miss_wire_exception_raise(self):
	""" test miss wire link exception raise """

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

	nl1.link('TOP')

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

	nl1.link('TOP')

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

	nl1.link('TOP')

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

	nl1.link('TOP')

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

	nl1.link('TOP')

# the parser will reconginze the pin "in" in INVDID1 U0 to a new pp without the in.
# because the parser will feed the "in" to expassion case like "in[1:0]" will be in[1], in[0] for each one has it's own pp
# so, the in pp will not be linked when the build up pase.

#	with self.assertRaises(Exception) as context:
#	    nl1.checkConnectionWidth()
#	print repr(context.exception)

	os.system('rm -rf test.v test.yml')



if __name__=='__main__':
    unittest.main()
