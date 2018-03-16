.setcallreg r3.w2
.origin 0

.macro nop
	mov	r0.b0, r0.b0
.endm

	slp	0
	add	r0, r0, r1
	halt
