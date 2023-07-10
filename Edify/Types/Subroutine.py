##############################################################################
#IMPORTS
##############################################################################
import sys
from dataclasses import field

from Edify.Types.EdifyObject import EdifyObject
from Edify.Types.Param       import Param
from Edify.Types.Step        import Step
from Edify.Types.Subflow     import Subflow

from ..Utils.Parsers import parseDetails, parseParamTable, parseObjectsTable, parseXcptnHndlrTbl
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
BAD_WORKSPACE_LIST_TABLE_FORMAT=1
UNEXPECTED_KEYS=2

##############################################################################
#GLOBALS
##############################################################################
errCode_=NONE

##############################################################################
#CLASSES
##############################################################################
class Subroutine(Subflow):
  def __init__(
    self,
    name: str,
    steps: list[Step] = field(default_factory=list),
    exceptionWorkspaces: list[str] = None,
    calledBy: list[str] = None,
    #prob unecessary: type: str = 'workspace/subroutine/exceptionHandler',
    entryParams: list[Param] = None,
    
    #dict[errorCode, exceptionHandlerName]
    exceptionHandlerMap: dict[str, str] = None,
    
    localObjs: list[EdifyObject] = None,    
    subflows: list[Subflow] = None
  ):
    super().__init__(name=name, steps=steps, subflows=subflows)
    self.exceptionWorkspaces: list[str] = exceptionWorkspaces
    self.calledBy: list[str] = calledBy
    #prob unecessary: self.type: str = type
    self.entryParams: list[Param] = entryParams
    
    #dict[errorCode, exceptionHandlerName]
    self.exceptionHandlerMap: dict[str, str] = exceptionHandlerMap
    
    self.localObjs: list[EdifyObject] = localObjs
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #TODO: merger fromWsHeader(...) with fromWorkspaceLstTableRow(...)
  #----------------------------------------------------------------------------
  @classmethod
  def fromWsHeader(ObjClass, wsHeader):
    name                = ObjClass._Subflow__getName(wsHeader)
    steps, err          = ObjClass._Subflow__getSteps(wsHeader, name)
    entryParams, err    = ObjClass.__getParams(wsHeader, name)
    localObjs, err      = ObjClass.__getLocalObjs(wsHeader, name)
    subflows            = ObjClass._Subflow__getSubflows(wsHeader, steps, name)
    exceptionHandlerMap = ObjClass.__getExceptionHandlerMap(wsHeader, name)
    
    newObj = ObjClass(
      name        = name,
      steps       = steps,
      entryParams = entryParams.split(' , ') if splittable(entryParams) else entryParams,
      localObjs   = localObjs.split(' , ') if splittable(localObjs) else localObjs,
      subflows    = subflows,
      exceptionHandlerMap = exceptionHandlerMap
    )
    
    return newObj, err
  #end fromWsHeader(wsHeader)
  
  #TODO: merger fromWsHeader(...) with fromWorkspaceLstTableRow(...)
  #----------------------------------------------------------------------------
  @classmethod
  def fromWorkspaceLstTableRow(SubroutineObjClass, row):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 2:
      errCode_ = errCode_ & BAD_WORKSPACE_LIST_TABLE_FORMAT
      print(
        'WARNING: "Workspace List" table has '
        'unexpected number of columns'
      )
    #end if unexpected # of cols
    
    name = cols[0].find('strong').text.strip()
    detailsDict = parseDetails(cols[1])
    #uncomment to test unexpectedKeys
    ##detailsDict['testUnexpected'] = 'testUnexpected'
    Subroutine.__warnIfUnexpectedWorkspaceDetails(name, detailsDict)
    
    newExceptionWs = detailsDict.get("Exception Workspaces")
    newCalledBy    = detailsDict.get("Called by")
    
    newSubroutine = SubroutineObjClass(
      name = name,
      exceptionWorkspaces = newExceptionWs.split(' , ') if splittable(newExceptionWs) else newExceptionWs,
      calledBy = newCalledBy.split(' , ') if splittable(newCalledBy) else newCalledBy
    ) #end newSubroutine SubroutineObjClass()
    
    return newSubroutine, errCode_
  #end fromWorkspaceLstTableRow(SubroutineObjClass, row)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __warnIfUnexpectedWorkspaceDetails(name, detailsDict):
    EXPECTED_KEYS = { "Exception Workspaces", "Called by" }
    
    #set difference
    unexpectedKeys = detailsDict.keys() - EXPECTED_KEYS      
    if unexpectedKeys:
      errCode_ = errCode_ & UNEXPECTED_KEYS
      print(
        f'WARNING: unexpected Workspace details for workspace with name '
        f'"{name}". Detail property names: {unexpectedKeys}',
        file=sys.stderr
      )
    #end if unexpectedKeys
  #end __warnIfUnexpectedWorkspaceDetails(name, detailsDict)
  
  # #----------------------------------------------------------------------------
  # @staticmethod
  # def __findWsTable(wsHeader, tblCaptionStrtTxt):
    # #loop thru sibling tags until next header
    # for tag in wsHeader.next_siblings:
      # if tag.name == wsHeader.name:
        # break
      
      # captions = tag.find_all('caption')
      # for caption in captions:
        # if caption.text.strip().startswith(tblCaptionStrtTxt):
          # return caption.find_parent('table')
    # #loop thru sibling tags until next header
    
    # #if didn't find right table
    # return None
  # #end __findWsTable(wsHeader, tblName)
  
  # #----------------------------------------------------------------------------
  # @staticmethod
  # def __getSteps(wsHeader, wsName):
    # stepLst = []
    
    # stepTable = Subroutine.fineWsTable(wsHeader, 'Steps')
    # if not stepTable:
      # return stepLst
    
    # stepLst, err = Subroutine.__parseStepTable(stepTable, wsName)
    
    # return stepLst, err
  # #end __getSteps(wsHeader, wsName)
  
  # #----------------------------------------------------------------------------
  # @staticmethod
  # def __parseStepTable(table, wsName):
    # stepLst = []
    
    # rows = table.find_all('tr')
    # #loop thru global objects
    # for row in rows:
      # newObj, err = Step.fromStepTableRow(row, wsName)
      # stepLst.append(newObj)
    # #end loop thru global objects
    
    # return stepLst, err
  # #end __parseStepTable(table, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getParams(wsHeader, wsName):
    paramLst = []
    errCode = NONE
    
    #paramTable = Subroutine.__findParamTable(wsHeader)
    paramTable = Subroutine.findWsTable(wsHeader, 'Entry Parameters')
    if not paramTable:
      return paramLst, errCode
    
    paramLst, err = parseParamTable(paramTable, wsName)
    errCode = errCode & err #forward all errors
    
    return paramLst, errCode
  #end __getParams(wsHeader, name)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getLocalObjs(wsHeader, wsName):
    objLst = []
    err = 0
    
    localObjTable = Subroutine.findWsTable(wsHeader, 'Local Objects')
    if not localObjTable:
      return objLst, err
    
    objLst, err = parseObjectsTable(localObjTable, wsName)
    
    return objLst, err
  #end __getLocalObjs(wsHeader)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getExceptionHandlerMap(wsHeader, wsName):
    handlerMap = {}
    
    xcptnHndlrTbl = Subroutine.findWsTable(wsHeader, 'Exception Handling Table')
    if not xcptnHndlrTbl:
      return handlerMap
    
    handlerMap = parseXcptnHndlrTbl(xcptnHndlrTbl, wsName)
    
    return handlerMap
  #end __getExceptionHandlerMap(wsHeader, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getSubflows(wsHeader, wsName):
    subflowLst = []
    err = 0
    
    
    
    return subflowLst, err
  #end __getLocalObjs(wsHeader, wsName)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "name="                + (f"{repr(self.name)}")
      + ", exceptionWorkspaces=" + (f"{repr(self.exceptionWorkspaces)}")
      + ", calledBy="            + (f"{repr(self.calledBy)}")
      #prob uneceessary: + ", type=" + (f"'{self.type}'"    if self.type                else "None")
      + ", entryParams="         + (f"{repr(self.entryParams)}")
      + ", exceptionHandlerMap=" + (f"{repr(self.exceptionHandlerMap)}")
      + ", localObjs="           + (f"{repr(self.localObjs)}")
      + ", steps="               + (f"{repr(self.steps)}")
      + ", subflows="            + (f"{repr(self.subflows)}")
      + ")"
    )
  #end __repr__(self)
#end Subroutine

class EntryWorkspace(Subroutine):
  pass
#end class EntryWorkspace

class ExceptionHandler(Subroutine):
  pass
#end class ExceptionHandler
