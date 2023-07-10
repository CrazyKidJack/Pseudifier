#TODO: fix error codes. All of them are bad even if they don't look like it!

##############################################################################
#IMPORTS
##############################################################################
import sys
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Any, List, TypeAlias

import Edify.Types as Types
from Edify.Types.EdifyObject import EdifyObject
from Edify.Types.Param       import Param
from Edify.Types.Step        import Step
from Edify.Types.Subflow     import Subflow
from Edify.Types.Subroutine  import Subroutine, EntryWorkspace, ExceptionHandler

from Edify.Utils.Parsers   import parseDetails, parseParamTable, parseObjectsTable
from Edify.Utils.Constants import GLOBAL_WS_NAME

import os
oldPath = sys.path
sys.path.append(r'..')
from pyUtils.io import promptForFile
sys.path = oldPath

##############################################################################
#CONSTANTS
##############################################################################
#err codes
NONE=0
FILE_PATH_EMPTY=1
PROPS_NOT_FOUND=2
ENTRY_WORKSPACE_NOT_FOUND=4
SUBROUTINES_NOT_FOUND=8
EXCEPTION_HANDLERS_NOT_FOUND=16
BAD_PROPS_TABLE_FORMAT=32
BAD_PARAM_TABLE_FORMAT=64
BAD_OBJ_TABLE_FORMAT=128
UNEXPECTED_OBJ_KEYS=256
UNEXPECTED_PARAM_KEYS=512
BAD_WORKSPACE_LIST_TABLE_FORMAT=1024
META_PARAMETER_PROP=2048

##############################################################################
#GLOBALS
##############################################################################
errCode_=NONE

##############################################################################
#CLASSES
##############################################################################
class AppObject:
  def __init__(
    self,
    props, globalObjs, subroutines
  ):
    self.props       = props
    self.globalObjs  = globalObjs
    self.subroutines = subroutines
  #end __init_(self, html)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  @classmethod
  def fromHtml(AppObjObjClass, html):
    soup = BeautifulSoup(html, "html.parser")
    
    props       = AppObjObjClass.parseProps(soup)
    globalObjs  = AppObjObjClass.parseGlobalObjects(soup)
    subroutines = AppObjObjClass.parseSubroutines(soup)
    
    return AppObjObjClass(
      props=props,
      globalObjs=globalObjs,
      subroutines=subroutines
    )
  #end fromHtml(AppObjObjClass, html)
  
  #returns dectionary of application object properties
  @staticmethod
  def parseProps(soup):
    metaProps = AppObject.__getMetaProps(soup)
    AppObject.__warnIfParamsConflict(metaProps)
    
    params = AppObject.__getAppObjParams(soup)
    
    return metaProps | {'parameters': params}
  #end parseProps(soup)
  
  #returns dictionary of app obj meta properties
  @staticmethod
  def __getMetaProps(soup):
    propsHeader = AppObject.__findPropsHeader(soup)
    if not propsHeader:
      errCode_ = errCode_ & PROPS_NOT_FOUND
      cleanNExit(
        'could not find "Application Object Properties" header...'
        'terminating...'
      )
    #end if not propsHeader
    
    return AppObject.__parseMetaPropsTable(propsHeader)
  #end __getMetaProps(soup)
  
  @staticmethod
  def __findPropsHeader(soup):
    headers = soup.find_all('h2')
    #loop thru headers to find app obj props
    for header in headers:
      if header.text.strip() == 'Application Object Properties':
        return header
    #end loop thru headers to find app obj props
    
    #if didn't find the right header
    return None
  #end __findPropsHeader(soup)
  
  @staticmethod
  def __parseMetaPropsTable(propsHeader):
    props = {}
    
    center = propsHeader.find_next_sibling('center')
    if not center:
      return props
      
    table = center.find('table')
    if not table:
      return props
    
    rows = table.find_all('tr')
    #loop thru meta props to get keys and vals
    for row in rows:
      key = row.find('th').text.strip()
      val = row.find('td').text.strip()
      props[key] = val
    #end loop thru meta props to get keys and vals
    
    return props
  #end __parseMetaPropsTable(propsHeader)
  
  #warns user if a "parameters" meta property exists simultaneously
  #  with "application object parameters"
  @staticmethod
  def __warnIfParamsConflict(metaProps):
    #if 'parameters' props conflict
    if 'parameters' in metaProps:
      errCode_ = errCode_ & META_PARAMETER_PROP
      print(
        'WARNING: application object has meta-property named "parameters". '
        'Cannot safely merge with "Application Object Parameters" table.'
      )
    #end if 'parameters' conflict
  #end __warnIfParamsConflict(metaProps)
  
  #returns list of app obj params
  @staticmethod
  def __getAppObjParams(soup):
    paramLst = []
    
    paramTable = AppObject.__findAppObjParamTable(soup)
    if not paramTable:
      return paramLst
    
    paramLst, errCode = parseParamTable(paramTable, GLOBAL_WS_NAME)    
    return paramLst
  #end __getAppObjParams(soup)
  
  @staticmethod
  def __findAppObjParamTable(soup):
    captions = soup.find_all('caption')
    #loop thru captions to find app obj param table
    for caption in captions:
      if caption.text.strip() == 'Application Object Parameters':
        return caption.find_parent('table')
    #end loop thru captions to find app obj param table
    
    #if didn't find right table
    return None
  #end __findAppObjParamTable(soup)
  
  #contents of this method could be replaced by __getGlobalObjects(soup)
  #  but not done to keep consistent with props
  @staticmethod
  def parseGlobalObjects(soup):
    objLst = AppObject.__getGlobalObjects(soup)
    
    return objLst
  #end parseGlobalObjects(soup)
  
  #contents of this method could be in parseGlobalObjects(soup)
  #  but put here to keep consistent with props
  @staticmethod
  def __getGlobalObjects(soup):
    objLst = []
    
    globalObjTable = AppObject.__findGlobalObjTable(soup)
    if not globalObjTable:
      return objLst
    
    objLst, err = parseObjectsTable(globalObjTable, GLOBAL_WS_NAME)
    return objLst
  #end __getGlobalObjects(soup)
  
  @staticmethod
  def __findGlobalObjTable(soup):
    captions = soup.find_all('caption')
    #loop thru captions to find global obj table
    for caption in captions:
      if 'Global Objects' in caption.text:
        return caption.find_parent('table')
    #end loop thru captions to find global obj table
    
    #if didn't find right table
    return None
  #end __findGlobalObjTable(soup)
  
  #TODO: merge lists
  @staticmethod
  def parseSubroutines(soup):
    wsLst = AppObject.__getWorkspaces(soup)
    
    wsLst = AppObject.__getSubroutines(soup)
    
    return wsLst
  #end parseSubroutines(soup)
  
  @staticmethod
  def __getWorkspaces(soup):
    wsLst = []
    
    wsLstTable = AppObject.__findWorkspaceLstTable(soup)
    if not wsLstTable:
      return wsLst
    
    wsLst = AppObject.__parseWorkspaceLstTable(wsLstTable)
    return wsLst
  #end __getWorkspaces(soup)
  
  @staticmethod
  def __findWorkspaceLstTable(soup):
    captions = soup.find_all('caption')
    #loop thru captions to find global obj table
    for caption in captions:
      if 'Workspace List' in caption.text:
        return caption.find_parent('table')
    #end loop thru captions to find global obj table
    
    #if didn't find right table
    return None
  #end __findWorkspaceLstTable(soup)
  
  @staticmethod
  def __parseWorkspaceLstTable(table):
    subroutineLst = []
    
    rows = table.find_all('tr')
    #loop thru rows of "Workspace List" table
    for row in rows:
      newSubroutine, err = Subroutine.fromWorkspaceLstTableRow(row)
      
      if err == Types.Subroutine.NONE:
        pass
      elif err == Types.Subroutine.BAD_WORKSPACE_LIST_TABLE_FORMAT:
        errCode_ = errCode_ & BAD_WORKSPACE_LIST_TABLE_FORMAT
      elif err == Types.Subroutine.UNEXPECTED_KEYS:
        errCode_ = errCode_ & UNEXPECTED_OBJ_KEYS
      
      subroutineLst.append(newSubroutine)
    #end loop thru rows of "Workspace List" table
    
    return subroutineLst
  #end __parseWorkspaceLstTable(table)
  
  @staticmethod
  def __getSubroutines(soup):
    subroutineLst = []
    
    entryWorkspaceHeader = AppObject.__findEntryWorkspaceHeader(soup)
    if not entryWorkspaceHeader:
      errCode_ = errCode_ & ENTRY_WORKSPACE_NOT_FOUND
      cleanNExit(
        'could not find "Entry Workspace" header...'
        'terminating...'
      )
    #end if not entryWorkspaceHeader
    
    subroutineHeaderLst = AppObject.__findSubroutineHeaders(soup)
    if not subroutineHeaderLst:
      errCode_ = errCode_ & SUBROUTINES_NOT_FOUND
      print(
        'WARNING: could not find ANY "Subroutine" headers...',
        file=sys.stderr
      )
    #end if not subroutineHeaderLst
    
    exceptionHandlerHeaderLst = AppObject.__findExceptionHandlerHeaders(soup)
    if not subroutineHeaderLst:
      errCode_ = errCode_ & EXCEPTION_HANDLERS_NOT_FOUND
      print(
        'WARNING: could not find ANY "Exception Handler" headers...',
        file=sys.stderr
      )
    #end if not subroutineHeaderLst
    
    
    #parse subroutines and add to list
    
    subroutineLst.append(AppObject.__parseEntryWorkspace(entryWorkspaceHeader))
    
    #loop thru "Subroutine" headers
    for header in subroutineHeaderLst:
      subroutineLst.append(AppObject.__parseSubroutine(header))
    #end loop thru "Subroutine" headers
    
    #loop thru "Exception Handler" headers
    for header in exceptionHandlerHeaderLst:
      subroutineLst.append(AppObject.__parseExceptionHandler(header))
    #end loop thru "Exception Handler" headers
    
    return subroutineLst
  #end __getSubroutines(soup)
  
  @staticmethod
  def __findEntryWorkspaceHeader(soup):
    headers = soup.find_all('h2')
    #loop thru headers to find app obj props
    for header in headers:
      if header.text.strip().startswith('Entry Workspace'):
        return header
    #end loop thru headers to find app obj props
    
    #if didn't find the right header
    return None
  #end __findEntryWorkspaceHeader(soup)
  
  @staticmethod
  def __findSubroutineHeaders(soup):
    subroutineHeaderLst = []
    
    headers = soup.find_all('h2')
    #loop thru headers to find app obj props
    for header in headers:
      headerText = header.text.strip()
      if headerText.startswith('Subroutine'):
        subroutineHeaderLst.append(header)
    #end loop thru headers to find app obj props
    
    return subroutineHeaderLst
  #end __findSubroutineHeaders(soup)
  
  @staticmethod
  def __findExceptionHandlerHeaders(soup):
    exceptionHandlerHeaderLst = []
    
    headers = soup.find_all('h2')
    #loop thru headers to find app obj props
    for header in headers:
      if header.text.strip().startswith('Exception Handler'):
        exceptionHandlerHeaderLst.append(header)
    #end loop thru headers to find app obj props
    
    return exceptionHandlerHeaderLst
  #end __findExceptionHandlerHeaders(soup)
  
  #TODO: determind if this function is needed
  #  seems like EntryWorkspace.fromWsHeader() is serving the purpose this funciton would usually serve
  @staticmethod
  def __parseEntryWorkspace(wsHeader):
    global errCode_
    newEntryWorkspace, err = EntryWorkspace.fromWsHeader(wsHeader)
    errCode_ = errCode_ & err
    return newEntryWorkspace
  #end __parseEntryWorkspace(wsHeader)
  
  #TODO: determind if this function is needed
  #  seems like Subroutine.fromWsHeader() is serving the purpose this funciton would usually serve
  @staticmethod
  def __parseSubroutine(subroutineHeader):
    global errCode_
    newSubroutine, err = Subroutine.fromWsHeader(subroutineHeader)
    errCode_ = errCode_ & err
    return newSubroutine
  #end __parseEntryWorkspace(subroutineHeader)
  
  #TODO: determind if this function is needed
  #  seems like ExceptionHandler.fromWsHeader() is serving the purpose this funciton would usually serve
  @staticmethod
  def __parseExceptionHandler(exceptionHandlerHeader):
    global errCode_
    newExceptionHandler, err = ExceptionHandler.fromWsHeader(exceptionHandlerHeader)
    errCode_ = errCode_ & err
    return newExceptionHandler
  #end __parseEntryWorkspace(exceptionHandlerHeader)
  
  ####################
  # INSTANCE METHODS #
  ####################
  # #----------------------------------------------------------------------------
  # def __repr__(self):
    # return (
      # f"{self.__class__.__name__}("
      # +   "name="                + (f"{repr(self.name)}")
      # + ", exceptionWorkspaces=" + (f"{repr(self.exceptionWorkspaces)}")
      # + ", calledBy="            + (f"{repr(self.calledBy)}")
      # #prob uneceessary: + ", type=" + (f"'{self.type}'"    if self.type                else "None")
      # + ", entryParams="         + (f"{repr(self.entryParams)}")
      # + ", exceptionHandlerMap=" + (f"{repr(self.exceptionHandlerMap)}")
      # + ", localObjs="           + (f"{repr(self.localObjs)}")
      # + ", steps="               + (f"{repr(self.steps)}")
      # + ", subflows="            + (f"{repr(self.subflows)}")
      # + ")"
    # )
  # #end __repr__(self)
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "props="  + (f"{repr(self.props)}")
      + ", globalObjs=" + (f"{repr(self.globalObjs)}")
      + ", subroutines=" + (f"{repr(self.subroutines)}")
      + ")"
    )
  #end __repr(self)__
# end class AppObject

##############################################################################
#FUNCTIONS
##############################################################################
#-----------------------------------------------------------------------------
def cleanNExit(msg=None, file=sys.stderr):
  if msg:
    print(msg, file=file)
  
  sys.exit(errCode_)
#end cleanNExit(msg, file)

#-----------------------------------------------------------------------------
def closeParagraphs(html):
  return html.replace('<p>', '<p></p>')
#end closeParagraphs(html)

##############################################################################
#MAIN
##############################################################################
filePath = promptForFile()
if filePath == "":
  errCode_ = errCode_ & FILE_PATH_EMPTY
  cleanNExit('Selected file path cannot be empty... terminating...')
#end if filePath empty

# Load the HTML file
with open(filePath, 'r') as inFile:
  html = inFile.read()

html = closeParagraphs(html)
appObj = AppObject.fromHtml(html)

# Print the data
print('Number of Properties:', len(appObj.props))
print('Properties:', appObj.props)
print()
print('Number of Properties.parameters:', len(appObj.props['parameters']))
print('Properties.parameters:', appObj.props['parameters'])
print()
print('Number of Global Objects:', len(appObj.globalObjs))
print('Global Objects:', appObj.globalObjs)
print('Global Objects[0]:', appObj.globalObjs[0])
print()
print('Number of Workspaces:', len(appObj.subroutines))
print('Workspaces:', appObj.subroutines)
print('Workspaces[0]:', appObj.subroutines[0])
print()
print()
print('Application Object:')
print(repr(appObj))

cleanNExit()
##############################################################################
#END MAIN
##############################################################################
