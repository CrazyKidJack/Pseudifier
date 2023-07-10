__all__=['parseDetails']
##############################################################################
#IMPORTS
##############################################################################
# import sys, os
# print(__file__)
# print()
# print(os.path.abspath(__file__))
# print()
# print(sys.path)
# print()
# oldPath = sys.path
# sys.path.append(os.path.dirname(__file__))
# print(sys.path)

# sys.exit(0)

#import ..Utils.Constants
#from ..Utils.Constants import ALL_WHITESPACE_STR

##############################################################################
#FUNCTIONS
##############################################################################
#-----------------------------------------------------------------------------
def parseDetails(detailCol):
  detailsDict = {}
  
  key = None
  val = ''
  #loop thru strings in detailCol to parse individual details
  for string in detailCol.strings:
    string = str(string) #convert to standard python unicode string
    #if string is name of key
    if string.endswith(': ') and not string.endswith(':: '):
      #if a key:val detail is waiting to be added to dict
      #  val could be empty
      if key:
        detailsDict = __addDetailToDict(detailsDict, key, val)
      #end if a key:val detail is waiting to be added to dict
      
      key = string
      val = ''
      continue
    #end if string is name of key
    
    #else in val
    val += string
  #end loop thru strings in detailCol to parse individual details
  
  #uncomment to test detail with no val
  ##val = ''
  
  #add last detail
  detailsDict = __addDetailToDict(detailsDict, key, val)
  
  return detailsDict
#end parseDetails(detailCol)

#-----------------------------------------------------------------------------
def __addDetailToDict(detailsDict, key, val):
  from ..Utils.Constants import ALL_WHITESPACE_STR
  
  #this looks weird because we want to ensure
  #  default whitespace stripping in addition to ',' and ':'
  key = key.strip(ALL_WHITESPACE_STR + ':,')
  val = val.strip(ALL_WHITESPACE_STR + ',')
  return detailsDict | {key: val}
#end __addDetailToDict(detailsDict, key, val)

#-----------------------------------------------------------------------------
def parseParamTable(paramTable, wsName):
  import Edify.Types as Types
  from Edify.Types.Param import Param
  
  paramLst = []
  errCode = Types.Param.NONE
  
  rows = paramTable.find_all('tr')
  #loop thru rows of app obj param table
  for row in rows:
    newParam, err = Param.fromParamTableRow(row, wsName)
    errCode = errCode & err #forward all errors
    
    paramLst.append(newParam)
  #end loop thru rows of app obj param table
  
  return paramLst, errCode
#end parseParamTable(paramTable, wsName)

#-----------------------------------------------------------------------------
def parseObjectsTable(table, wsName):
  from Edify.Types.EdifyObject import EdifyObject
  
  objLst = []
  err = None
  
  rows = table.find_all('tr')
  #loop thru global objects
  for row in rows:
    newObj, err = EdifyObject.fromObjTableRow(row, wsName)
    objLst.append(newObj)
  #end loop thru global objects
  
  return objLst, err
#end parseObjectsTable(table, wsName)

#-----------------------------------------------------------------------------
def parseXcptnHndlrTbl(table, wsName):
  handlerMap = {}
  
  rows = table.find_all('tr')
  #loop thru exception code mappings
  for row in rows:
    #if unexpected num of cols
    if (len(row.find_all('td')) != 1) or (len(row.find_all('th')) != 1):
      print(
        'ERROR: unexpected number of columns in "Exception Handling Table" '
        f'for workspace with name: "{wsName}". Terminating...'
      )
      sys.exit(0)
    #end if unexpected num of cols
    
    codeCol = row.th
    nameCol = row.td
    
    xcptnCode = codeCol.text.strip()
    name      = nameCol.a.text.strip()
    ref       = (nameCol.a)['href']
    
    handlerMap[xcptnCode] = f"{name}:{ref}"
  #end loop thru exception code mappings
  
  return handlerMap
#end parseXcptnHndlrTbl(table, wsName)