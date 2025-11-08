#!/usr/bin/env python3
from ctypes import cdll
import ctypes

# Load the shared library
lib = cdll.LoadLibrary('./lingo.so')

lib.add.argtypes = [ctypes.c_int, ctypes.c_int]
lib.add.restype = ctypes.c_int

# Call the Go function
result = lib.add(10, 20)
print(f'Result from C function: {result}')