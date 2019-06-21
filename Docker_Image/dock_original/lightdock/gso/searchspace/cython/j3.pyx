"""J3: circles function"""

#cython: boundscheck=False
#cython: wraparound=False

from libc.math cimport sin, pow

def j3(double x, double y):
    return pow(x*x + y*y,0.25) * (pow(sin(50.0*pow(x*x + y*y,0.1)),2) + 1.0)
