##############################################################################
#IMPORTS
##############################################################################
import sys
from dataclasses import field
from typing import Any

from ..Utils.Parsers import parseDetails
from ..Utils.Constants import GLOBAL_WS_NAME

import os
oldPath = sys.path
sys.path.append(r'..')
from pyUtils.Strings import splittable
sys.path = oldPath

##############################################################################
#CONSTANTS
##############################################################################
#err codes
NONE=0
BAD_OBJ_TABLE_FORMAT=1
UNEXPECTED_KEYS=2

##############################################################################
#GLOBALS
##############################################################################
errCode_=NONE

##############################################################################
#CLASSES
##############################################################################
class EdifyObject:
  def __init__(
    self, name: str, ref: str, objClass: str,
    comment: str = None, initialValue:str = None, resource:str = 'no',
    usedBy: list[str] = field(default_factory=list),
    preAlloc: str = None, autoAlloc: str = None,
    _sys_alloc_name: str = None, _sys_alloc_timeout: str = None
  ):
    self.name: str     = name
    self.ref: str       = ref
    self.objClass: str = objClass
    self.comment: str      = comment
    self.initialValue: Any = initialValue
    self.resource: str     = resource
    self.usedBy: list[str] = usedBy
    self.preAlloc: str           = preAlloc
    self.autoAlloc: str          = autoAlloc
    self._sys_alloc_name: str    = _sys_alloc_name
    self._sys_alloc_timeout: str = _sys_alloc_timeout
  #end __init__(...)
  
  @classmethod
  def fromObjTableRow(EdifyObjectClass, row, wsName):
    if wsName == GLOBAL_WS_NAME:
      return EdifyObject.__fromGlobalObjTableRow(row)
    else:
      return EdifyObject.__fromLocalObjTableRow(row, wsName)
  #end fromObjTableRow(EdifyObjectClass, row, wsName)
  
  @classmethod
  def __fromLocalObjTableRow(EdifyObjectClass, row, wsName):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 2:
      errCode_ = errCode_ & BAD_OBJ_TABLE_FORMAT
      print(
        f'WARNING: "Local Objects" table from workspace "{wsName}" '
        f'has unexpected number of columns'
      )
    #end if unexpected # of cols
    
    name = cols[0].strong.text.strip()
    ref   = (cols[0].strong.find_parent('a'))['name']
    
    detailsDict = parseDetails(cols[1])
    #uncomment to test unexpected keys
    ##detailsDict['testUnexpected'] = 'testUnexpected'
    EdifyObject.__warnIfUnxpctdLocalObjDetails(name, detailsDict, wsName)
    
    newUsedBy = detailsDict.get("Used by")
    
    newObj = EdifyObjectClass(
      name = name,
      ref = ref,
      objClass = detailsDict.get("Object Class", ""),
      comment = detailsDict.get("Comment"),
      initialValue = detailsDict.get("Initial Value"),
      resource = detailsDict.get("resource"),
      preAlloc = detailsDict.get("pre-allocate"),
      autoAlloc = detailsDict.get("auto-allocate"),
      _sys_alloc_name = detailsDict.get("_sys_alloc_name"),
      _sys_alloc_timeout = detailsDict.get("_sys_alloc_timeout"),
      usedBy = newUsedBy.split(' , ') if splittable(newUsedBy) else newUsedBy
    ) #end newObj EdifyObjectClass()
    
    return newObj, errCode_
  #end fromLocalObjTableRow(EdifyObjectClass, row, wsName)
  
  @classmethod
  def __fromGlobalObjTableRow(EdifyObjectClass, row):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 2:
      errCode_ = errCode_ & BAD_OBJ_TABLE_FORMAT
      print(
        'WARNING: "Global Objects" table has '
        'unexpected number of columns'
      )
    #end if unexpected # of cols
    
    name = cols[0].strong.text.strip()
    ref   = (cols[0].strong.find_parent('a'))['name']
    
    detailsDict = parseDetails(cols[1])
    #uncomment to test unexpected keys
    ##detailsDict['testUnexpected'] = 'testUnexpected'
    EdifyObject.__warnIfUnxpctdGlobalObjDetails(name, detailsDict)
    
    newUsedBy = detailsDict.get("Used by")
    
    newObj = EdifyObjectClass(
      name = name,
      ref   = ref,
      objClass = detailsDict.get("Object Class", ""),
      comment = detailsDict.get("Comment"),
      initialValue = detailsDict.get("Initial Value"),
      resource = detailsDict.get("resource"),
      preAlloc = detailsDict.get("pre-allocate"),
      autoAlloc = detailsDict.get("auto-allocate"),
      _sys_alloc_name = detailsDict.get("_sys_alloc_name"),
      _sys_alloc_timeout = detailsDict.get("_sys_alloc_timeout"),
      usedBy = newUsedBy.split(' , ') if splittable(newUsedBy) else newUsedBy
    ) #end newObj EdifyObjectClass()
    
    return newObj, errCode_
  #end fromGlobalObjTableRow(EdifyObjectClass, row)
  
  @staticmethod
  def __warnIfUnxpctdLocalObjDetails(name, detailsDict, wsName):
    EXPECTED_KEYS = {
      "Object Class", "Comment", "Initial Value", "resource",
      "pre-allocate", "auto-allocate", "_sys_alloc_name", "_sys_alloc_timeout",
      "Used by"
    }
    
    #set difference
    unexpectedKeys = detailsDict.keys() - EXPECTED_KEYS      
    if unexpectedKeys:
      errCode_ = errCode_ & UNEXPECTED_KEYS
      print(
        f'WARNING: unexpected Local Object details for object '
        f'from workspace "{wsName}" with name "{name}".'
        f'Detail property names: {unexpectedKeys}',
        file=sys.stderr
      )
    #end if unexpectedKeys
  #end __warnIfUnxpctdLocalObjDetails(name, detailsDict, wsName)
  
  @staticmethod
  def __warnIfUnxpctdGlobalObjDetails(name, detailsDict):
    EXPECTED_KEYS = {
      "Object Class", "Comment", "Initial Value", "resource",
      "pre-allocate", "auto-allocate", "_sys_alloc_name", "_sys_alloc_timeout",
      "Used by"
    }
    
    #set difference
    unexpectedKeys = detailsDict.keys() - EXPECTED_KEYS      
    if unexpectedKeys:
      errCode_ = errCode_ & UNEXPECTED_KEYS
      print(
        f'WARNING: unexpected Global Object details for object with name '
        f'"{name}". Detail property names: {unexpectedKeys}',
        file=sys.stderr
      )
    #end if unexpectedKeys
  #end __warnIfUnxpctdGlobalObjDetails(name, detailsDict)
  
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "name="               + (f"{repr(self.name)}")
      + ", ref="                 + (f"{repr(self.ref)}")
      + ", objClass="           + (f"{repr(self.objClass)}")
      + ", comment="            + (f"{repr(self.comment)}")
      + ", initialValue="       + (f"{repr(self.initialValue)}")
      + ", resource="           + (f"{repr(self.resource)}")
      + ", usedBy="             + (f"{repr(self.usedBy)}")
      + ", preAlloc="           + (f"{repr(self.preAlloc)}")
      + ", autoAlloc="          + (f"{repr(self.autoAlloc)}")
      + ", _sys_alloc_name="    + (f"{repr(self._sys_alloc_name)}")
      + ", _sys_alloc_timeout=" + (f"{repr(self._sys_alloc_timeout)}")
      + ")"
    )
  #end __repr__(self)
#end class EdifyObject