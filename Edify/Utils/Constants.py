##############################################################################
#CONSTANTS
##############################################################################
ALL_WHITESPACE_STR = ''
d = 0
c = None
#loop thru dec char values
while True:
  try:
    c = chr(d)
  except ValueError:
    break
  
  if c.isspace():
    ALL_WHITESPACE_STR += c
  
  d += 1
#end loop thru dec char values

GLOBAL_WS_NAME = 'Global'