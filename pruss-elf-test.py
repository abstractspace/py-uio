#!/usr/bin/python3

from ti.icss import Icss
from ctypes import c_uint32
import struct

pruss = Icss( "/dev/uio/pruss/module" )
pruss.initialize()

core = pruss.core0

# load program
with open('pruss-elf-test-fw/test.out', 'rb') as f:
    pruss.elf_load( core, f.read() )

# map shared memory
shmem = pruss.dram2.map( c_uint32 )

print( shmem.value )

core.run()

print( "waiting for core to halt" )
while not core.halted:
    pass

print( shmem.value )
