##############################################################################
#IMPORTS
##############################################################################
from typing import Any

from ..Utils.Constants import GLOBAL_WS_NAME

##############################################################################
#CONSTANTS
##############################################################################
#err codes
NONE=0
BAD_PARAM_TABLE_FORMAT=1

##############################################################################
#GLOBALS
##############################################################################
errCode_=NONE

##############################################################################
#CLASSES
##############################################################################
class Param:
  def __init__(
    self, name: str, label: str, objClass: str, ioType: str, defaultVal: Any
  ):
    self.name: str       = name
    self.label: str      = label
    self.objClass: str   = objClass
    self.ioType: str     = ioType
    self.defaultVal: Any = defaultVal
  #end __init__(...)
  
  @classmethod
  def fromParamTableRow(ParamObjClass, row, wsName):
    if wsName == GLOBAL_WS_NAME:
      return Param.__fromGlobalParamTableRow(row)
    else:
      return Param.__fromWsParamTableRow(row, wsName)
  #end fromParamTableRow(ParamObjClass, row, wsName)
  
  @classmethod
  def __fromWsParamTableRow(ParamObjClass, row, wsName):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 5:
      errCode_ = errCode_ & BAD_PARAM_TABLE_FORMAT
      print(
        f'WARNING: "Entry Parameters" table from workspace "{wsName}" '
        f'has unexpected number of columns'
      )
    #end if unexpected # of cols
    
    newParam = Param(
      name       = cols[0].text.strip(),
      label      = cols[1].text.strip(),
      objClass   = cols[2].text.strip(),
      ioType     = cols[3].text.strip(),
      defaultVal = cols[4].text.strip(),
    )
    
    return newParam, errCode_
  #end __fromWsParamTableRow(ParamObjClass, row)
  
  @classmethod
  def __fromGlobalParamTableRow(ParamObjClass, row):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 5:
      errCode_ = errCode_ & BAD_PARAM_TABLE_FORMAT
      print(
        'WARNING: "Application Object Parameters" table has '
        'unexpected number of columns'
      )
    #end if unexpected # of cols
    
    newParam = Param(
      name       = cols[0].text.strip(),
      label      = cols[1].text.strip(),
      objClass   = cols[2].text.strip(),
      ioType     = cols[3].text.strip(),
      defaultVal = cols[4].text.strip(),
    )
    
    return newParam, errCode_
  #end __fromGlobalParamTableRow(ParamObjClass, row)
  
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "name="       + (f"{repr(self.name)}")
      + ", label="      + (f"{repr(self.label)}")
      + ", objClass="   + (f"{repr(self.objClass)}")
      + ", ioType="     + (f"{repr(self.ioType)}")
      + ", defaultVal=" + (f"{repr(self.defaultVal)}")
      + ")"
    )
  #end __repr__(self)
#end class Param