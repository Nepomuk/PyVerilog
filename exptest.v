
module TOP( in, out );

    output [  1: 0 ] out;
    output ECO_out
    input  [  1: 0 ] in;
    input ECO_in

    INVD1 U0( .I( in[0] ), .ZN( out[0] ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
    INVD1 ECO_INVD1( .I( ECO_in ), .ZN( ECO_out ) );
endmodule
