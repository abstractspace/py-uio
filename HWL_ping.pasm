.origin 0
.entrypoint main

#define DRDY	r31.t5
#define DCLK	r31.t4
#define D0	r5.t3
#define D1	r5.t2
#define D2	r5.t1
#define D3	r5.t0

.struct Params
	.u32	start
	.u32	end
.ends

.assign Params, r18, r19, params

#define ptr r20

// can't name these "T0" or "T1" since those are reserved keywords
#define T0_OUT	r30.t6
#define T1_OUT	r30.t7

.macro set_if
.mparam dst, src
        qbbc    skip, src
        set     dst
skip:
.endm

main:
    lbco	&params, c24, 0, SIZE(params)	// read buffer parameters
	mov	ptr, params.start		// initialize head pointer
    
wait: 
	wbs	DRDY	// wait until DRDY is high
    wbc DRDY    // once it goes low, begin collecting on next clock pulse

    
    loop end_first, 32      // loop through the first 32 data bits
    wbs	DCLK                // wait for DCLK to go high
    lsl r10, r10, 1         // shift data  0000 -> 0 000x -? 00 00xy
    lsl r12, r12, 1
    lsl r14, r14, 1
    lsl r16, r16, 1
    wbc DCLK                // wait till the DCLK goes low
    set	T0_OUT	            // set T0 low
    mov r5, r31             // store r31 (input pins)
    set_if r10.t0, D0
    set_if r12.t0, D1
    set_if r14.t0, D2
    set_if r16.t0, D3 
    clr	T0_OUT	            // set T0 high
end_first:                 // the first 32 bits have been received
 

    loop end_second, 32    // loop through the second 32 data bits
    wbs	DCLK               // wait for DCLK to go high
    lsl r11, r11, 1        // shift data  0000 -> 0 000x -? 00 00xy
    lsl r13, r13, 1
    lsl r15, r15, 1
    lsl r17, r17, 1
    wbc DCLK              // wait till the DCLK goes low
    set	T1_OUT	// set T1 high
    mov r5, r31           // store r31 (input pins)
    set_if r11.t0, D0
    set_if r13.t0, D1
    set_if r15.t0, D2
    set_if r17.t0, D3 
    clr	T1_OUT	// set T1 low
end_second:               // the second 32 bits have been received

	sbbo	&r10, ptr, 0, 8*4
	add	ptr, ptr, 8*4
	qbne	still_space, ptr, params.end
	mov	ptr, params.start
still_space:
	sbbo	&ptr, params.end, 0, 4	// store the head pointer
    
	jmp	wait
    