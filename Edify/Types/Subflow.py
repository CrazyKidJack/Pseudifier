##############################################################################
#IMPORTS
##############################################################################
import sys
from dataclasses import field
from typing import Any

from Edify.Types.Step import Step, SubflowStep

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
class Subflow:
  def __init__(
    self,
    name: str,
    steps: list[Step] = field(default_factory=list),
    subflows: list['Subflow'] = None
  ):
    self.name: str = name
    self.steps: list[step] = steps
    self.subflows: list['Subflow'] = subflows
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromWsHeader(ObjClass, wsHeader):
    name       = ObjClass.__getName(wsHeader)
    steps, err = ObjClass.__getSteps(wsHeader, name)
    subflows   = ObjClass.__getSubflows(wsHeader, steps, name)
    
    newObj = ObjClass(
      name = name,
      steps = steps,
      subflows = subflows
    )
    
    return newObj
  #end fromWsHeader(ObjClass, wsHeader)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def findWsTable(wsHeader, tblCaptionStrtTxt):
    #loop thru sibling tags until next header
    for tag in wsHeader.next_siblings:
      if tag.name == wsHeader.name:
        break
      
      #if tag is searchable
      if callable(getattr(tag, 'find_all', None)):
        captions = tag.find_all('caption')
        for caption in captions:
          if caption.text.strip().startswith(tblCaptionStrtTxt):
            return caption.find_parent('table')
    #loop thru sibling tags until next header
    
    #if didn't find right table
    return None
  #end __findWsTable(wsHeader, tblName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getName(wsHeader):
    return wsHeader.a.text.strip()
  #end __getName(wsHeader)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getSteps(wsHeader, wsName):
    stepLst = []
    
    stepTable = Subflow.findWsTable(wsHeader, 'Steps')
    if not stepTable:
      return stepLst
    
    stepLst, err = Subflow.__parseStepTable(stepTable, wsName)
    
    return stepLst, err
  #end __getSteps(wsHeader, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseStepTable(table, wsName):
    stepLst = []
    
    rows = table.find_all('tr')
    #loop thru global objects
    for row in rows:
      newObj, err = Step.fromStepTableRow(row, wsName)
      stepLst.append(newObj)
    #end loop thru global objects
    
    return stepLst, err
  #end __parseStepTable(table, wsName)
  
  #----------------------------------------------------------------------------
  #depends on already having a list of Step objects
  #  for the workspace with name wsName and header wsHeader
  @staticmethod
  def __getSubflows(wsHeader, steps, wsName):
    subflowLst = []
    
    headerLst = Subflow.__findSubflowHeaders(wsHeader, steps, wsName)
    
    for header in headerLst:
      subflowLst.append(Subflow.fromWsHeader(header))
    
    
    return subflowLst
  #end __getSubflows(wsHeader, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getSubflowRefs(wsHeader, steps, wsName):
    refSet = set()
    
    #loop thru steps looking for subflow invocations
    for step in steps:
      if type(step) is not SubflowStep:
        continue
      #else this step invokes a subflow, get ref
      
      #get the part after the last colon (:) char
      #  and then remove the leading pound sign char (#)
      targetRef = ((step.target.rsplit(':', 1))[1])[1:]
      
      refSet.add(targetRef)
    #end loop thru steps looking for subflow invocations
    
    return refSet
  #end __getSubflowRefs(wsHeader, steps, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __findSubflowHeaders(wsHeader, steps, wsName):
    headerLst = []
    
    refSet = Subflow.__getSubflowRefs(wsHeader, steps, wsName)
    if not refSet:
      return headerLst
    
    #loop thru headers in soup to find any subflow header
    #  invoked by workspace with header wsHeader and name wsName
    for header in wsHeader.find_next_siblings('h2'):
      #if header has an <a> tag
      if header.a:
        headerRef = header.a.get('name')
        #if found header for subflow invoked by this workspace
        if headerRef in refSet:
          headerLst.append(header)
          #if found headers for all invoked subflows
          if len(headerLst) == len(refSet):
            break
          #end if found headers for all invoked subflows          
        #end if found header for subflow invoked by this workspace
      #end if header has an <a> tag
    #end loop thru headers in soup to find any subflow header
    #  invoked by workspace with header wsHeader and name wsName
    
    #if didn't find Subflow headers for all invoked subflows
    if not len(headerLst) == len(refSet):
      print(
        f'WARNING: Could not find headers for all subflows invoked by workspace "{wsName}"...\n'
        'List of subflow headers (headerLst) = \n'
        f'{repr(headerLst)}\n'
        '\n'
        'list of refs to invoked subflows (refSet) = \n'
        f'{repr(refSet)}'
      )
    #end if didn't find Subflow headers for all invoked subflows
    
    return headerLst
  #end __findSubflowHeaders(wsHeader, steps, wsName)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "name="  + (f"{repr(self.name)}")
      + ", steps=" + (f"{repr(self.steps)}")
      + ")"
    )
  #end __repr__(self)
#end class Subflow