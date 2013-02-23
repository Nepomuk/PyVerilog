module TOP( in, out );

    input  [  1: 0 ] in;
    output [  1: 0 ] out;

    wire ECO_0;

    INVD1 U0( .I( ECO_0 ), .ZN( out[0] ) );
    INVD1 U1( .I( in[1] ), .ZN( out[1] ) );
    INVD1 ECO_INVD1( .I( in[0] ), .ZN( ECO_0 ) );
endmodule
