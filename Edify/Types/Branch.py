##############################################################################
#IMPORTS
##############################################################################
import sys
from dataclasses import dataclass

##############################################################################
#CLASS
##############################################################################
@dataclass
class Branch:
  id       : int
  condition: str
  targetLoc: str
  sourceObj   : str = None
  comparisonOp: str = None
  targetObj   : str = None
#end dataclass Branch