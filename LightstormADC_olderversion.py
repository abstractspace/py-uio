#!/usr/bin/python3

from ti.icss import Icss
from ctypes import c_uint32
import ctypes
import time
import numpy as np
from subprocess import run
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.GPIO as GPIO

# setup PRU pins
run(['config-pin',  'P8.39',  'pruout'])
run(['config-pin',  'P8.40',  'pruout'])
run(['config-pin',  'P8.41',  'pruin'])
run(['config-pin',  'P8.42',  'pruin'])
run(['config-pin',  'P8.43',  'pruin'])
run(['config-pin',  'P8.44',  'pruin'])
run(['config-pin',  'P8.45',  'pruin'])
run(['config-pin',  'P8.46',  'pruin'])

# setup SPI
# WARNING, may need to change P.17 to spi_cs and P9.22 to spi_sclk for newest Debian release
# run(['config-pin',  'P9.17',  'spi_cs'])
run(['config-pin',  'P9.17',  'spi']) 
run(['config-pin',  'P9.18',  'default']) # can't have MOSI high during power up, so we will configure as SPI after power up
run(['config-pin',  'P9.21',  'spi'])
# run(['config-pin',  'P9.22',  'spi_slck'])
run(['config-pin',  'P9.22',  'spi']) 

# setup other enable pins and reset pins
ADC_PWR_EN_PIN = 'P8_19'
ADC_RESET_PIN = 'P8_17'
ADC_RUN_PIN = 'P8_18'
GPIO.setup(ADC_PWR_EN_PIN, GPIO.OUT)
GPIO.setup(ADC_RESET_PIN, GPIO.OUT)  # reset is active low
GPIO.setup(ADC_RUN_PIN, GPIO.OUT)

GPIO.output(ADC_PWR_EN_PIN, GPIO.HIGH)
GPIO.output(ADC_RESET_PIN, GPIO.LOW)    # pulse reset after startup ( datasheet says to do this)
GPIO.output(ADC_RUN_PIN, GPIO.HIGH)

time.sleep(0.5)
GPIO.output(ADC_RUN_PIN, GPIO.LOW)
time.sleep(0.5)
GPIO.output(ADC_RUN_PIN, GPIO.HIGH)
GPIO.output(ADC_RESET_PIN, GPIO.HIGH)   # ADC powered up now, wait a second before starting SPI transfers
time.sleep(1) 

# SPI Adafruit library: https://github.com/adafruit/adafruit-beaglebone-io-python/blob/master/docs/SPI.rst
#print(spi.xfer2([(0b10000000 | 0x11), 0x00])) # read register 0x11
run(['config-pin',  'P9.18', 'spi']) # can't have MOSI high during power up, so now configure as SPI
spi = SPI(0, 0)

#print(spi.xfer2([(0b00000000 | 0x11), 0b01110100])) # write register 0x11 low power mode (8kHz), internal reference on 
print(spi.xfer2([(0b00000000 | 0x11), 0b01110100])) # write register 0x11 high power mode (16kHz), internal reference on 
print(spi.xfer2([(0b00000000 | 0x15), 0b01000000])) # write register 0x15, internal reference

# To compile firmware, use the command: pasm -b -V3 HWL_ping.pasm
pruss = Icss( "/dev/uio/pruss/module" )
pruss.initialize()

core = pruss.core1 # CORE 1!!!!

# load program
with open('HWL_ping.bin', 'rb') as f:
    core.iram.write( f.read() )

NUM_SAMPLES = 5000

class Shmem( ctypes.Structure ):
    _fields_ = [
            ("buf",     c_uint32 * 8 * NUM_SAMPLES),
            ("head",    c_uint32),
        ]
shmem = pruss.ddr.map( Shmem )
shmem.address = pruss.ddr.address

class Params( ctypes.Structure ):
    _fields_ = [
            ("start",   c_uint32),
            ("end",     c_uint32),
        ]
params = core.dram.map( Params )

params.start = shmem.address
params.end = shmem.address + ctypes.sizeof( shmem.buf )

tail = 0

# run pru program
core.run()

start = time.time()
while (time.time() - start <= 1.0):
    head = (shmem.head - shmem.address) // ctypes.sizeof( shmem.buf[0] )
    while head != tail:
        #frame = shmem.buf[tail]
        tail += 1
        if tail == NUM_SAMPLES:
            tail = 0
            break
        # do stuff with frame
        
end = time.time()
core.halt()

print('Collection time in seconds:')
print(end-start)

# no need to have so many numpy arrays actually
x = np.asarray(shmem.buf, dtype=np.uint32)  
y = x << 8
z = np.asarray(y, dtype=np.int32)
w = z >> 8

# in case you want to check the data looks reasonable
print('CH 0-8 at row 117:')
for elem in x[117]:
    print(bin(elem))
    print(hex(elem))

np.savetxt("test_on_bbb.csv", w, delimiter=",")