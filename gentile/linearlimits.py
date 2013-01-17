"""
Liner limit the layer size of cube pruning.

the numbers is N, but it should <= 5, so it means we only limit first five layers.

the function is y=-50x+b, and the integration from 1 to N should equals 1.5*cubesize
"""

def linearlimits(n, size):
  """
  Calculate parameter a and b of the function.
  return a list of limit for each layer.
  """
  if n > 5:
    n = 5
  b = (1.5*size+25*(n+1)*(n+1)-25)/(n)
  limits = [-50*i+b for i in range(1, n+1)]
  return limits