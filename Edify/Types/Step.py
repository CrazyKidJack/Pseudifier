##############################################################################
#IMPORTS
##############################################################################
import sys
from dataclasses import field
from typing import Any

from Edify.Types.Branch import Branch
from Edify.Types.EdifyObject import EdifyObject

from ..Utils.Constants import ALL_WHITESPACE_STR

##############################################################################
#CONSTANTS
##############################################################################
#err codes
NONE=0
BAD_STEP_TABLE_FORMAT=1
UNEXPECTED_KEYS=2
UNEXPECTED_STEP_TYPE=4
UNEXPECTED_DETAILS=8

##############################################################################
#GLOBALS
##############################################################################
errCode_=NONE

##############################################################################
#CLASSES
##############################################################################
##############################################################################
#abstract
class Step:
  def __init__(
    self, id: str, ref: str, label: str = None
  ):
    self.id:    str = id
    self.ref:   str = ref
    self.label: str = label
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableRow(StepObjClass, row, wsName):
    global errCode_
    cols = row.find_all('td')
    #if unexpected # of cols
    if len(cols) != 2:
      errCode_ = errCode_ & BAD_STEP_TABLE_FORMAT
      print(
        f'WARNING: "Steps" table in workspace with name {wsName} '
        'has unexpected number of columns'
      )
    #end if unexpected # of cols
    
    id     = StepObjClass.__getId(cols[0])
    ref    = StepObjClass.__getRef(cols[0])
    type   = StepObjClass.__getType(cols[0])
    
    newStep = None
    
    #switch on step type
    if type == 'Subflow':
      newStep = SubflowStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Start':
      newStep = StartStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Use System Function':
      newStep = UseSystemFunctionStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Call DLL':
      newStep = CallDllStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Choose':
      newStep = ChooseStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Assign':
      newStep = AssignStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Call':
      newStep = CallStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'Goto':
      newStep = GotoStep.fromStepTableCols(cols, id, ref, wsName)
    elif type == 'End':
      newStep = EndStep.fromStepTableCols(cols, id, ref, wsName)
    else:
      print(
        f'ERROR: Unexpected step type at {wsName}::{id}... terminating...'
      )
      errCode_ = errCode_ & UNEXPECTED_STEP_TYPE
      sys.exit(errCode_)
    #end switch on step type
    
    return newStep, errCode_
  #end fromStepTableRow(row, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getId(col):
    #get the text inside the first strong in the column
    return col.strong.text.strip()
  #end __getId(col)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getRef(col):
    #get val of name prop of first a tag in first strong tag in the column
    return col.strong.a['name']
  #end __getRef(col)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getType(col):
    #get the text right before the first line break in the column
    return col.br.previous_sibling.text.strip(ALL_WHITESPACE_STR+'.')
  #end __getType(col)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getLabel(col, wsName, id):
    colTextLines = col.text.split('\n')
    numLines = len(colTextLines)
    #if no label line
    if numLines == 1:
      return None
    elif numLines > 2: #elif unexpected # of lines
      print(
        f"WARNING: {len(colTextLines)} lines in step {wsName}::{id} "
        'is more than the 2 expected lines.\n'
        'Only keeping 1 line that starts with "Label" for Label prop. '
        'Label prop may not be accurate.'
      )
    #end if no label line elif unexpected
    
    for line in colTextLines:
      if line.startswith('Label:'):
        label = (line.partition(': '))[2]
        return label
  #end __getLabel(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getTarget(col):
    #loop thru tags in col after 1st strong, before 1st br
    for tag in col.strong.next_sibling.next_elements:
      if tag.name == 'br':
        break
      
      if tag.name == 'a':
        return tag.text.strip()
    #end loop thru tags in col after 1st strong, before 1st br  
    
    return None
  #end __getTarget(col)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="  + (f"{repr(self.id)}")
      + ", ref=" + (f"{repr(self.ref)}")
      + ", label=" + (f"{repr(self.label)}")
      + ")"
    )
  #end __repr(self)__
# end class Step

##############################################################################
class SubflowStep(Step):
  type = 'Subflow'
  
  def __init__(
    self, id: str, ref: str, target: str, label: str = None,
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.target: str = target
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(SubflowStepObjClass, cols, id, ref, wsName):
    target = SubflowStepObjClass.__getTarget(cols[1])
    label  = SubflowStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = SubflowStepObjClass(id=id, ref=ref, target=target, label=label)
    return newStep
  #end fromStepTableRow(cols, id, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getTarget(col):
    name = col.a.text.strip()
    ref = col.a['href']
    return f"{name}:{ref}"
  #end __getTarget(col)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="  + (f"{repr(self.id)}")
      + ", ref=" + (f"{repr(self.ref)}")
      + ", type="   + (f"{repr(self.type)}")
      + ", label="  + (f"{repr(self.label)}")
      + ", target=" + (f"{repr(self.target)}")
      + ")"
    )
  #end __repr(self)__
#end class SubflowStep

##############################################################################
class StartStep(Step):
  type = 'Start'
  
  def __init__(
    self,
    id: str, ref: str, params: dict[str, str] = None,
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.params = params
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(StartStepObjClass, cols, id, ref, wsName):
    params = StartStepObjClass.__getParams(cols[1], wsName, id)
    label  = StartStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = StartStepObjClass(id=id, ref=ref, params=params, label=label)
    return newStep
  #end fromStepTableCols(StartStepObjClass, cols, id, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getParams(col, wsName, id):
    global errCode_
    paramDict = {}
    
    inParams = False
    key = ''
    warned = False
    #loop thru strings in col
    for strng in col.strings:
      #if col doens't start with params
      if not inParams and not strng.startswith('Parameters'):
        if not warned:
          print(
            f"WARNING: Start step at {wsName}::{id} "
            "has unexpected details before 'Parameters'"
          )
          warned = True
        #end if not warned
        errCode_ = errCode_ & UNEXPECTED_DETAILS
        continue
      #end if col doens't start with params
      
      #if Parameters = <none>
      if strng.startswith('Parameters ='):
        inParams = True
        key = 'Parameters'
        continue
      
      if strng.startswith('Parameters'):
        inParams = True
        continue
      
      #if there's a key waiting for a value, this must be a value
      if key:
        ref=None
        if key != 'Parameters':
          ref = (strng.find_parent('a'))['href']
        val = strng if not strng.endswith(', ') else ((strng.rpartition(', '))[0])
        paramDict[key] = val+f":{ref}"
        key = ''
        continue
      #end if there's a key waiting for a value, this must be a value
      
      #TODO: find a more robust way to identify keys
      #if found a key, and don't already have one waiting
      if strng.endswith(' = '):
        key = (strng.rpartition(' = '))[0]
        continue
      #end if found a key
      
      if strng == ', ':
        continue
      
      #here we know it isn't a key, value, or separator
      #  must be done
      break
    #end loop thru strings in col
    
    return paramDict    
  #end __getParams(col)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="  + (f"{repr(self.id)}")
      + ", ref=" + (f"{repr(self.ref)}")
      + ", type=" + (f"{repr(self.type)}")
      + ", label=" + (f"{repr(self.label)}")
      + ", params=" + (f"{repr(self.params)}")
      + ")"
    )
  #end __repr(self)__
#end class StartStep

##############################################################################
class UseSystemFunctionStep(Step):
  type = 'Use System Function'
  
  def __init__(
    self, id: str, ref: str, funcName: str, label: str = None,
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.funcName: str = funcName
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(UseSystemFunctionStepObjClass, cols, id, ref, wsName):
    funcName = UseSystemFunctionStepObjClass.__getFuncName(cols[1], wsName, id)
    label  = UseSystemFunctionStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = UseSystemFunctionStepObjClass(id=id, ref=ref, funcName=funcName, label=label)
    return newStep
  #end fromStepTableRow(cols, id, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getFuncName(col, wsName, id):
    funcName = (col.text.strip().split('\n'))[0]
    #if didn't find function name
    if not funcName.startswith('Function Name'):
      print(
        "WARNING: could not find function name in first line of step detail "
        f"for step {wsName}::{id}."
      )
      return None
    #end if didn't find function name
    
    funcName = (funcName.partition(' = '))[2]
    return funcName
  #end __getFuncName(col)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="       + (f"{repr(self.id)}")
      + ", ref="     + (f"{repr(self.ref)}")
      + ", type="     + (f"{repr(self.type)}")
      + ", label="    + (f"{repr(self.label)}")
      + ", funcName=" + (f"{repr(self.funcName)}")
      + ")"
    )
  #end __repr(self)__
#end class UseSystemFunctionStep(Step)

##############################################################################
class CallDllStep(Step):
  type = 'Call DLL'
  
  def __init__(
    self, id: str, ref: str,
    funcName: str, prototype: str, args: dict[str, str],
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.funcName: str = funcName
    self.prototype: str = prototype
    self.args: list[str] = args
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(CallDllStepObjClass, cols, id, ref, wsName):
    funcName  = CallDllStepObjClass.__getFuncName(cols[1], wsName, id)
    prototype = CallDllStepObjClass.__getPrototype(cols[1], wsName, id)
    args      = CallDllStepObjClass.__getArgs(cols[1], wsName, id)
    label     = CallDllStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = CallDllStepObjClass(
      id=id, ref=ref,
      funcName=funcName, prototype=prototype, args=args,
      label=label
    )
    return newStep
  #end fromStepTableCols(CallDllStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getFuncName(col, wsName, id):
    funcNameLine = CallDllStep.__findDetailLinePrefix(col, 'Library Name')
    
    #if not found function name
    if not funcNameLine:
      print(
        "WARNING: could not find function name in step detail "
        f"for step {wsName}::{id}."
      )
      return None
    #end if not found function name
    
    funcName = CallDllStep.__parseFuncName(funcNameLine)    
    return funcName
  #end __getFuncName(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __findDetailLinePrefix(col, prefix):
    detailLine = None
    colDetailLines = col.text.strip().split('\n')
    #loop thru find function name line
    for line in colDetailLines:
      if line.startswith(prefix):
        detailLine = line
        break
    #end loop thru find function name line
    
    return detailLine
  #end __findFuncNameLine(col)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseFuncName(funcNameLine):
    funcNameParts = funcNameLine.split(', ')
    funcName = ''
    #loop thru 1st line details to build funcName
    for part in funcNameParts:
      partVal = (part.partition(' = '))[2]
      if funcName:
        funcName = funcName + '::'
      funcName = funcName + partVal.strip('"')
    #end loop thru 1st line details to build funcName
    
    return funcName
  #end __parseFuncName(funcNameLine)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getPrototype(col, wsName, id):
    prototypeLine = CallDllStep.__findDetailLinePrefix(col, 'Function Prototype')
    
    #if not found prototype
    if not prototypeLine:
      print(
        "WARNING: could not find prototype in step detail "
        f"for step {wsName}::{id}."
      )
      return None
    #end if not found prototype
    
    prototype = CallDllStep.__parsePrototype(prototypeLine)    
    return prototype
  #end __getPrototype(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parsePrototype(prototypeLine):
    prototype = (prototypeLine.partition(' = '))[2]
    return prototype
  #end __parsePrototype(prototypeLine)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getArgs(col, wsName, id):
    argFont = CallDllStep.__findArgFont(col)
    
    #if not found args
    if not argFont:
      print(
        "WARNING: could not find args in step detail "
        f"for step {wsName}::{id}."
      )
      return None
    #end if not found args
    
    argDict = CallDllStep.__parseArgs(argFont)
    return argDict
  #end __getArgs(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __findArgFont(col):
    argFont = None
    
    for tag in col.find_all('strong'):
      if tag.text.strip().startswith('Function Args'):
        argFont = tag.find_parent('font')
    
    return argFont
  #end __findArgFont(col)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseArgs(argFont):
    argDict = {}
    
    key = ''
    #loop thru arg tags
    for keyTag in argFont.find_all('em'):
      key = keyTag.text.strip()
      valTag = keyTag.find_next_sibling('font')
      ref  = valTag.a['href']
      val = valTag.text.strip() + f":{ref}"
      argDict[key] = val
    #end loop thru arg tags
    
    return argDict
  #end __parseArgs(argFont)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="        + (f"{repr(self.id)}")
      + ", ref="       + (f"{repr(self.ref)}")
      + ", type="      + (f"{repr(self.type)}")
      + ", label="     + (f"{repr(self.label)}")
      + ", funcName="  + (f"{repr(self.funcName)}")
      + ", prototype=" + (f"{repr(self.prototype)}")
      + ", args="      + (f"{repr(self.args)}")
      + ")"
    )
  #end __repr(self)__
#end class CallDllStep

##############################################################################
class ChooseStep(Step):
  type = 'Choose'
  
  def __init__(
    self, id: str, ref: str,
    branches: list[Branch] = field(default_factory=list),
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.branches = branches
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(ChooseStepObjClass, cols, id, ref, wsName):
    branches = ChooseStepObjClass.__getBranches(cols[1], wsName, id)
    label    = ChooseStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = ChooseStepObjClass(
      id=id, ref=ref,
      branches=branches,
      label=label
    )
    return newStep
  #end fromStepTableCols(ChooseStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getBranches(col, wsName, id):
    branchLst = []
    
    branchStrongLst = col.find_all('strong')
    #loop thru branch strongs searching for starts
    for strong in branchStrongLst:
      strongText = strong.text.strip()
      #if not a valid start of a branch definition
      if not strong.text.strip().startswith('Branch #'):
        continue
      #end if not a valid start of a branch definition
      
      branchId = strongText[8:-1]
      condition = strong.next_sibling.text.strip()
      detailsDict = ChooseStep.__getBranchDetails(strong, wsName, id, branchId)
      
      newBranch = Branch(
        id=branchId, condition=condition,
        **detailsDict
      )
      
      branchLst.append(newBranch)
    #end loop thru branch stongs searching for starts
    
    return branchLst
  #end __getBranches(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getBranchDetails(strong, wsName, id, branchId):
    branchDetailsDict = {}
    
    branchDetailLineStrt = strong.find_next('br').next_sibling
    key = ''
    val = ''
    ref = None
    #loop thru branch details
    for tag in branchDetailLineStrt.next_siblings:
      if tag.name == 'br':
        break
      
      tagStr = tag.text
      
      #if separator
      if tagStr == ', ':
        continue
      #end if separator
      
      #if key tag
      if tagStr.endswith(' = '):
        key = (tagStr.rpartition(' = '))[0]
        continue
      #end if key tag
      
      #if have key waiting and this is not a key
      if key:
        tagStrStrip = tagStr.strip()
        val = tagStrStrip if not tagStrStrip.endswith(',') else tagStrStrip[:-1]
        ref = ChooseStep.__parseRef(tag, wsName, id, branchId)
        
        key = ChooseStep.__shortenKey(key)
        branchDetailsDict[key] = f"{val}:{ref}"
        key = ''
        val = ''
        ref = None
        continue
      #end if have key waiting and this is not a key
    #end loop thru branch details
    
    return branchDetailsDict
  #end __getBranchDetails(strong, wsName, id, branchId)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseRef(tag, wsName, id, branchId):
    ref = None
    
    #if this is a or has a link, get ref
    if tag.name == 'a':
      ref = tag['href']
    else:
      if callable(getattr(tag, 'find_all', None)):
        linkLst = tag.find_all('a')
        #if unxpctd # of links
        if len(linkLst) > 1:
          print(
            f"WARNING: Branch {branchId} in choose step {wsName}::{id} "
            "has multiple 'a' tags. Just using ref from first"
          )
        elif len(linkLst) < 1:
          print(
            f"WARNING: Branch {branchId} in choose step {wsName}::{id} "
            "has no 'a' tags."
          )
          
          return ref
        #end if unxpctd # of links, else
        
        ref = (linkLst[0])['href']
      #end if callable tag.find_all(...)
    #end if this is a link, else
    
    return ref
  #end __parseRef(tag, wsName, id, branchId)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __shortenKey(key):
    if key == 'Target Location':
      return 'targetLoc'
    elif key == 'Source Object':
      return 'sourceObj'
    elif key == 'Comparison Operator':
      return 'comparisonOp'
    elif key == 'Target Object':
      return 'targetObj'
    else:
      return key
  #end __shortenKey(key)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="       + (f"{repr(self.id)}")
      + ", ref="      + (f"{repr(self.ref)}")
      + ", type="     + (f"{repr(self.type)}")
      + ", label="    + (f"{repr(self.label)}")
      + ", branches=" + (f"{repr(self.branches)}")
      + ")"
    )
  #end __repr(self)__
#end class ChooseStep(Step)

##############################################################################
class AssignStep(Step):
  type = 'Assign'
  
  def __init__(
    self,
    id: str, ref: str,
    obj: EdifyObject, val: Any,
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.obj: EdifyObject = obj
    self.val: Any = val
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(AssignStepObjClass, cols, id, ref, wsName):
    obj   = AssignStepObjClass.__getObj(cols[0], wsName, id)
    val   = AssignStepObjClass.__getVal(cols[1], wsName, id)
    label = AssignStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = AssignStepObjClass(
      id=id, ref=ref,
      obj=obj, val=val,
      label=label
    )
    return newStep
  #end fromStepTableCols(AssignStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getObj(col, wsName, id):
    objLink = (col.find_all('a'))[1]
    name = objLink.text.strip()
    ref  = objLink['href']
    return f"{name}:{ref}"
  #end __getObj(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getVal(col, wsName, id):
    if col.text.strip().startswith('Expression = '):
      return AssignStep.__parseExpression(col, wsName, id)
    elif col.text.strip().startswith('Value = '):
      return AssignStep.__parseValue(col, wsName, id)
    else:
      print(
        f'ERROR: Unexpected details in AssignStep {wsName}::{id}. '
        'It does not start with "Expression = " or "Value = "\n'
        'Terminating...'
      )
      sys.exit(0)
  #end __getVal(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseExpression(col, wsName, id):
    detailDict = {}
    
    key = ''
    val = ''
    ref = None
    #loop thru strings in col
    for strng in col.strings:
      #if found key
      if strng.endswith(' = '):
        strText = strng.text.strip()
        key = strText[:-2]
        continue
      #end if found key
      
      #if key is waiting and this not key, this must be value
      if key:
        val = strng.text.strip(ALL_WHITESPACE_STR+',')
        linkParent = strng.find_parent('a')
        if linkParent:
          ref = linkParent['href']
        
        detailDict[key] = f"{val}:{ref}"
        
        key = ''
        val = ''
        ref = None
        continue
      #end if key is waiting and this not key, this must be value
    #end loop thru strings in col
    
    return detailDict
  #end __parseExpression(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __parseValue(col, wsName, id):
    valTag = col.em.next_sibling
    name = valTag.text.strip()
    ref = None
    
    #if valTag is a or has a link
    if valTag.name == 'a':
      ref = valTag['href']
    #elif callable valTag.find_all(...)
    elif callable(getattr(valTag, 'find_all', None)):
      linkLst = valTag.find_all('a')
      
      #if unxpctd # of links
      if len(linkLst) > 1:
        print(
          f"WARNING: Assign step {wsName}::{id} "
          "has multiple 'a' tags. Just using ref from first"
        )
      elif len(linkLst) < 1:
        print(
          f"WARNING: Assign step {wsName}::{id} "
          "has no 'a' tags."
        )
        
        return f"{name}:{ref}"
      #end if unxpctd # of links
      
      ref = (linkLst[0])['href']
    #end if valTag is a or has a link, elif
    
    return f"{name}:{ref}"
  #end __parseValue(col, wsName, id)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="    + (f"{repr(self.id)}")
      + ", ref="   + (f"{repr(self.ref)}")
      + ", type="  + (f"{repr(self.type)}")
      + ", label=" + (f"{repr(self.label)}")
      + ", obj="   + (f"{repr(self.obj)}")
      + ", val="   + (f"{repr(self.val)}")
      + ")"
    )
  #end __repr(self)__
#end class AssignStep(Step)

##############################################################################
class CallStep(Step):
  type = 'Call'
  
  def __init__(
    self,
    id: str, ref: str,
    target: str, params: dict[str, str] = None,
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.target: str = target
    self.params: dict[str, str] = params
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(CallStepObjClass, cols, id, ref, wsName):
    target = CallStepObjClass.__getTarget(cols[1], wsName, id)
    params = CallStepObjClass.__getParams(cols[1], wsName, id)
    label  = CallStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = CallStepObjClass(
      id=id, ref=ref,
      target=target, params=params,
      label=label
    )
    return newStep
  #end fromStepTableCols(CallStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getTarget(col, wsName, id):
    inTarget = False
    #loop thru strings in col to look for target
    for strng in col.strings:      
      #if found target header
      if strng.startswith('Target ') and strng.endswith(': '):
        inTarget = True
        continue
      #end if found target header
      
      if inTarget:
        name = strng.text
        ref  = strng.find_parent('a')['href']
        return f"{name}:{ref}"
    #end loop thru strings in col to look for target
    
    #if didn't find target
    print(
      f'WARNING: Call steps {wsName}::{id} '
      'does not have a target.'
    )
    return None
  #end __getTarget(col, wsName, id)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getParams(col, wsName, id):
    paramDict = {}
    
    key = ''
    val = ''
    ref = None
    inParams = False
    #loop thru strings in col to look for params
    for strng in col.strings:
      #if found params header
      if strng.startswith('Parameters:'):
        inParams = True
        continue
      #end if found params header
      
      if inParams:
        #if found key
        if strng.endswith(' = '):
          strText = strng.text.strip()
          key = strText[:-2]          
          continue
        #end if found key
        
        #if key waiting and this is not a key, then must be val
        if key:
          val = strng.text
          
          linkParent = strng.find_parent('a')
          if linkParent:
            ref = linkParent['href']
          
          paramDict[key] = f"{val}:{ref}"
          
          key = ''
          val = ''
          ref = None
          continue
        #end if key waiting and this is not a key, then must be val
    #end loop thru strings in col to look for params
    
    return paramDict
  #end __getParams(col, wsName, id)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="    + (f"{repr(self.id)}")
      + ", ref="   + (f"{repr(self.ref)}")
      + ", type="  + (f"{repr(self.type)}")
      + ", label=" + (f"{repr(self.label)}")
      + ", target="   + (f"{repr(self.target)}")
      + ", params="   + (f"{repr(self.params)}")
      + ")"
    )
  #end __repr(self)__
#end class CallStep(Step)

##############################################################################
class GotoStep(Step):
  type = 'Goto'
  
  def __init__(
    self,
    id: str, ref: str,
    target: str,
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.target: str = target
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(GotoStepObjClass, cols, id, ref, wsName):
    target = GotoStepObjClass.__getTarget(cols[1], wsName, id)
    label  = GotoStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = GotoStepObjClass(
      id=id, ref=ref,
      target=target,
      label=label
    )
    return newStep
  #end fromStepTableCols(GotoStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getTarget(col, wsName, id):
    inTarget = False
    #loop thru strings in col to look for target
    for strng in col.strings:      
      #if found target header
      if strng == 'Target Location = ':
        inTarget = True
        continue
      #end if found target header
      
      #if inTarget
      if inTarget:
        name = strng.text
        ref  = None
        
        linkParent = strng.find_parent('a')
        if linkParent:
          ref = linkParent['href']
        
        return f"{name}:{ref}"
      #end if inTarget
    #end loop thru strings in col to look for target
    
    #if didn't find target
    print(
      f'ERROR: Goto step {wsName}::{id} '
      'does not have a target.'
    )
    sys.exit(1)
  #end __getTarget(col, wsName, id)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="     + (f"{repr(self.id)}")
      + ", ref="    + (f"{repr(self.ref)}")
      + ", type="   + (f"{repr(self.type)}")
      + ", label="  + (f"{repr(self.label)}")
      + ", target=" + (f"{repr(self.target)}")
      + ")"
    )
  #end __repr(self)__
#end class GotoStep(Step)

##############################################################################
class EndStep(Step):
  type = 'End'
  
  def __init__(
    self,
    id: str, ref: str,
    rtnMode: str,
    label: str = None
  ):
    super().__init__(id=id, ref=ref, label=label)
    self.rtnMode: str = rtnMode
  #end __init__(...)
  
  ########################
  # STATIC/CLASS METHODS #
  ########################
  #----------------------------------------------------------------------------
  @classmethod
  def fromStepTableCols(EndStepObjClass, cols, id, ref, wsName):
    rtnMode = EndStepObjClass.__getRtnMode(cols[1], wsName, id)
    label  = EndStepObjClass._Step__getLabel(cols[0], wsName, id)
    
    newStep = EndStepObjClass(
      id=id, ref=ref,
      rtnMode=rtnMode,
      label=label
    )
    return newStep
  #end fromStepTableCols(EndStepObjClass, cols, id, ref, wsName)
  
  #----------------------------------------------------------------------------
  @staticmethod
  def __getRtnMode(col, wsName, id):
    inMode = False
    #loop thru strings in col to look for target
    for strng in col.strings:
      #if found rtnMode header
      if strng.lower() == 'return mode = ':
        inMode = True
        continue
      #end if found rtnMode header
      
      #if inMode
      if inMode:
        mode = strng.text
        return mode
      #end if inMode
    #end loop thru strings in col to look for target
    
    #if didn't find target
    print(
      f'ERROR: End step {wsName}::{id} '
      'does not have a return mode.'
    )
    sys.exit(1)
  #end __getRtnMode(col, wsName, id)
  
  ####################
  # INSTANCE METHODS #
  ####################
  #----------------------------------------------------------------------------
  def __repr__(self):
    return (
      f"{self.__class__.__name__}("
      +   "id="      + (f"{repr(self.id)}")
      + ", ref="     + (f"{repr(self.ref)}")
      + ", type="    + (f"{repr(self.type)}")
      + ", label="   + (f"{repr(self.label)}")
      + ", rtnMode=" + (f"{repr(self.rtnMode)}")
      + ")"
    )
  #end __repr(self)__
#end class EndStep(Step)