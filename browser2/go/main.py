#!/usr/bin/env python3
from ctypes import cdll
import ctypes

# Load the shared library
lib = cdll.LoadLibrary('./lingo.so')

lib.Add.argtypes = [ctypes.c_int, ctypes.c_int]
lib.Add.restype = ctypes.c_int

# Call the Go function
result = lib.Add(10, 20)
print(f'Result from Go function: {result}')
