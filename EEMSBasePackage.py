######################################################################
# EEMS Package
######################################################################

# EEMS is the Environmental Evaluation Modeling System. EEMS provides
# software framework to implement hierarchical (i.e. tree-based) fuzzy
# logic-base decision support models.
#
# To use EEMS, a user writes a program in the EEMS language, which
# consists of a small number of very explicit commands. The user's
# program is a logical representation of the hierarchical decision
# support tree. Data is read from files, the hierarchical logic applied,
# and results written.
#
# How data is read and written is unique to the file type. This, and
# possibly some other non-core aspects of model implementation are
# built on top of what is in this package. Central to the framework
# is extensive error checking and error messaging.
#
# Included in this package are:
#
# class EEMSCmd
#
# This class parses an EEMS command, checks if for correctness, and
# provides access to the command attributes and parameters.
#
# class EEMSProgram
#
# This class takes an EEMS command file (simply a text file containing
# the program the user wrote using the EEMS programming language), creates
# an EEMSCmd object for each EEMS command in the file, and arranges them
# into an order appropriate for dependency-ordered execution. EEMSProgram
# keeps a pointer to the current EEMSCmd, so that EEMSCmds can be stepped
# through during EEMS execution
#
# class EEMSCmdRunnerBase
#
# This class is where the meat of the computation takes place. It provides
# the data structures and functions to store and compute the values that
# correspond to the EEEMS commands. It does not, however provide any of the
# I/O functionality. This is specific to the type of data file. Use this
# as a parent class for the specific implementation
#
# class EEMSInterpreterBase
#
# This class is designed to coordinate an EEMSProgram object and an
# EEMSCmdRunner object. A specific implementation of EEMS will normally
# utilize an EEMSInterpreter object to execute the .eem file.
#
# History
#
# EEMS is derived from work orginally done at Conservation Biology
# Institute to mimic the functionality of EMDS under ArcGIS without the
# need for 3rd party software. Jim Strittholt directed the initial
# development with Tim Sheehan and Brendan Ward doing the programming.
#
# Since the initial development, Tim Sheehan has taken on EEMS as lead
# developer.
#
# Version 1.0 of EEMS was designed specifically to run with ArcGIS
# ModelBuilder and was implemented as several scripts specific to Arc.
# The EEMS language used in version 1.0 was cryptic and unsuitable for
# interactive use.
#
# Version 2.0 has been under development starting in December 2013 and
# continuing into February 2014.
#
# Significant features of EEMS 2.0 include:
#
# - Easy to understand, explicit EEMS programming language
# - Modular design as framework
# - Extensive error checking and messaging
# - Utilization of numpy library for fast computation
#
# The EEMS language was designed and implemented by, and this script was written by:
#
# Tim Sheehan
# Ecological Modeler
# Conservation Biology Institute
# www.consbio.org
#
# EEMS is based on the functionality of EMDS (http://www.spatial.redlands.edu/emds/)
#
# Contributors to EEMS include:
# Mike Gough, Conservation Biology Institute
# Brendan Ward, Conservation Biology Institute
# Jim Strittholt, Conservation Biology Institute
# Tosha Comendant, Conservation Biology Institute
#
# File History
#
# 2014.02.14 - tjs
#
# Individual classes and utilities combined into single file.
#
# 2015.09.09 = tjs
#
# Note this is a one-off version and is not for general release.
#
# This version is to be used with the eems explorer and for
# constructing "fake" .eem files created using CALLEXTERN.
#
# Added TWS version commands.
#
# Added CALLEXTERN command so that it can be parsed, but NOT executed.
# This was done as a means of using CALLEXTERN in an eems model
# presented with the eems explorer.
#
# Added fields to command descriptions:
#
#   ReadableNm
#   ShortDesc
#   RtrnType
#   InputType
#
######################################################################

import re
import numpy as np

######################################################################
# class EEMSCmd
######################################################################
#
# This class encapsulates an EEMS command. Its constructor takes a
# string and parses it into its parts, stored in the dictionary
# parsedCmd. Exhaustive error checking is performed in the parsing
#  process.
#
# Worth noting is that the syntax of an EEMS command string (user-
# generated) doesn't need any indicator of data type. For example
#  strings don't need to be quoted. Data typing of parameters is
# taken care of internally. In fact, all data is read as strings,
# but when a user requests command data using the GetParam() method,
# the data is converted to the correct type before it is returned.
#
# Revision History
#
# 2014.01.28 - tjs
#
# Completed writing and testing of this class. It appears to be ready
# to use with the EEMS for Arc python scripts, which will be modified to use this
# class.
#
# 2014.01.29 - tjs
#
# Cleaned up cmdDesc and some Get functions
#
# 2012.02.14 - tjs
#
# Added EMDSAND and WTDEMDSAND. Testing Complete
#
# 2015.01.19 - tjs
#
# Added 'NewFieldName' and 'NewFieldNames' optional parameters to
# READ and READMULTI. This allows for renaming input fields. This
# is useful if you are reading fields with the same name from
# different files.
######################################################################

class EEMSCmd(object):

    def __init__(self,cmdStr,showHelpOnly=False):

        self.cmdStr = cmdStr
        self.parsedCmd = None
        self.cmdDesc = None # Command description for checking and error messages
        self.__ParseEEMSCmd()
        self.__ValidateCmd()

    # def __init__(self,cmdStr):

    def __enter__(self):
        return self
    # def __enter__(self):

    # init command description lookup
    def __InitCmdDesc(self):
        # Command descriptions for checking and error messages
        # Every EEMS language command must be specified here.

        if self.parsedCmd['cmd'] in ['READ']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Required Params':{'InFileName':'File Name',
                                   'InFieldName':'Field Name'
                                   },
                'Optional Params':{'OutFileName':'File Name',
                                   'NewFieldName':'Field Name'
                                   },
                'ReadableNm':'Read',
                'ShortDesc':'Read a variable',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['READMULTI']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Required Params':{'InFileName':'File Name',
                                   'InFieldNames':'Field Name List'
                                   },
                'Optional Params':{'OutFileName':'File Name',
                                   'NewFieldNames':'Field Name List'
                                   },
                'ReadableNm':'Read Multiple Variables',
                'ShortDesc':'Read multiple variables from a singe file',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['CVTTOFUZZY']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name',
                                   'TrueThreshold':'Float',
                                   'FalseThreshold':'Float'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Convert To Fuzzy',
                'ShortDesc':'Convert input field into a fuzzy field using linear interpolation',
                'RtrnType':'Fuzzy',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['CVTTOFUZZYCURVE']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name',
                                   'RawValues':'Float List',
                                   'FuzzyValues':'Fuzzy Value List',
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Convert To Fuzzy Curve',
                'ShortDesc':'Convert input field into a fuzzy field using a curve function',
                'RtrnType':'Fuzzy',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['CVTTOFUZZYCAT']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name',
                                   'RawValues':'Float List',
                                   'FuzzyValues':'Fuzzy Value List',
                                   'DefaultFuzzyValue':'Float'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Convert To Fuzzy Category',
                'ShortDesc':'Convert input field into a fuzzy field using categorical lookup',
                'RtrnType':'Fuzzy',
                'InputType':'Integer'
                }
        elif self.parsedCmd['cmd'] in ['COPYFIELD']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Copy A Field',
                'ShortDesc':'Copies an existing field into a new field',
                'RtrnType':'Any',
                'InputType':'Any'
                }
        elif self.parsedCmd['cmd'] in ['NOT']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Not',
                'ShortDesc':'Returns the fuzzy logical negative of fuzzy input field',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['SELECTEDUNION']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'TruestOrFalsest':'Truest or Falsest',
                                   'NumberToConsider':'Positive Integer'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy Selected Union',
                'ShortDesc':'Returns the Union of the N Truest or Falsest fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['OR']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy Or',
                'ShortDesc':'Returns the Truest of fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['ORNEG']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy Negative Or',
                'ShortDesc':'Returns the Falsest of fuzzy input fields - Deprecated. Use And',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['XOR']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy Exclusive Or',
                'ShortDesc':'Returns the fuzzy logic equivalent of exclusive or of fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['SUM']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Sum',
                'ShortDesc':'Returns sum of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['MIN']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Minimum',
                'ShortDesc':'Returns minimum of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['MAX']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Maximum',
                'ShortDesc':'Returns maximum of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['MEAN']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Mean',
                'ShortDesc':'Returns mean of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['UNION']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy Union',
                'ShortDesc':'Returns the mean of fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['AND']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Fuzzy And',
                'ShortDesc':'Returns the minimum of fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['EMDSAND']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'EMDS And',
                'ShortDesc':'Applies the EMDS And function to fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['DIF']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'StartingFieldName':'Field Name',
                                   'ToSubtractFieldName':'Field Name'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Difference',
                'ShortDesc':'Takes the difference of two input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['WTDUNION']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'Weights':'Positive Float List'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Weighted Union',
                'ShortDesc':'Returns the weighted mean of fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['WTDMEAN']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'Weights':'Positive Float List'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Weighted Mean',
                'ShortDesc':'Returns the weighted mean of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['WTDSUM']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'Weights':'Positive Float List'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Weighted Sum',
                'ShortDesc':'Returns the weighted sum of input fields',
                'RtrnType':'Numeric',
                'InputType':'Numeric'
                }
        elif self.parsedCmd['cmd'] in ['WTDEMDSAND']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'Weights':'Positive Float List'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Weighted EMDS And',
                'ShortDesc':'Applies the Weighted EMDS And function to fuzzy input fields',
                'RtrnType':'Fuzzy',
                'InputType':'Fuzzy'
                }
        elif self.parsedCmd['cmd'] in ['CALLEXTERN']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldNames':'Field Name List',
                                   'ImportName':'Import Name',
                                   'FunctionName':'Function Name',
                                   'ResultType':'Field Type Description'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Call External Function',
                'ShortDesc':'Calls an external function',
                'RtrnType':'Any',
                'InputType':'Any'
                }
        elif self.parsedCmd['cmd'] in ['SCORERANGEBENEFIT']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Score Range Benefit',
                'ShortDesc':'Converts input field to fuzzy field using score range benefit algorithm',
                'RtrnType':'Fuzzy',
                'InputType':'Numeric'
            }
        elif self.parsedCmd['cmd'] in ['SCORERANGECOST']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name'},
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Score Range Cost',
                'ShortDesc':'Converts input field to fuzzy field using score cost benefit algorithm',
                'RtrnType':'Fuzzy',
                'InputType':'Numeric'
            }
        elif self.parsedCmd['cmd'] in ['MEANTOMID']:
            self.cmdDesc = {
                'Name':self.parsedCmd['cmd'],
                'Result':'Field Name',
                'Required Params':{'InFieldName':'Field Name',
                                   'IgnoreZeros':'Boolean',
                                   'FuzzyValues':'Fuzzy Value List'
                                   },
                'Optional Params':{'OutFileName':'File Name'},
                'ReadableNm':'Mean To Mid',
                'ShortDesc':'Converts input field to fuzzy field using mean to mid algorithm',
                'RtrnType':'Fuzzy',
                'InputType':'Numeric'
            }
        else:
            raise Exception (
                'Illegal Command: *%s*\n'%(self.parsedCmd['cmd'])+
                'Full erroneous command is:\n'+
                '  %s\n'%(self.cmdStr)+
                'Proper command format is:\n'+
                '  Result = Command(Parameter1 = ParameterValue1,...)')

    # def __InitCmdDesc(self):

    # To trim a string
    def __TrimEndSpace(self,str):
        return re.sub(r'\s*$','',re.sub(r'^\s*','',str))

    # Using regular expressions to test if a string comprises a valid variable using
    def __IsStrValidFileName(self,inStr):
        if re.match(r'([a-zA-Z]:[\\/]){0,1}[\w\\/\.\- ]*\w+\s*$',inStr):
            return True
        else:
            return False

    def __IsStrValidInt(self,inStr):
        if re.match(r'^[0-9]$',inStr):
            return True
        else:
            return False

    def __IsStrValidFloat(self,inStr):
        if re.match(r'^[+-]{0,1}([0-9]+\.*[0-9]*)$|(^[+-]{0,1}\.[0-9]+)$',inStr):
            return True
        else:
            return False

    def __IsStrValidBoolean(self,inStr):
        if (inStr in ['0','1','-1'] or
            re.match(r'^[Tt][Rr][Uu][Ee]$',inStr) or
                re.match(r'^[Ff][Aa][Ll][Ss][Ee]$',inStr)):
            return True
        else:
            return False

    def __IsStrValidFieldName(self,inStr):
        if re.match(r'^\w+$',inStr):
            return True
        else:
            return False

    def __IsStrValidFunctionName(self,inStr):
        if re.match(r'^\w+$',inStr):
            return True
        else:
            return False

    def __IsStrValidImportName(self,inStr):
        if re.match(r'([a-zA-Z_]){0,1}[\w\.\- ]*$',inStr):
            return True
        else:
            return False

    def __IsStrValidFldTypeDesc(self,inStr):
        if inStr in ['Fuzzy','Numeric','Any']:
            return True
        else:
            return False

    def __IsListParam(self,inStr):
        if re.match(r'^\[.+\]$',inStr):
            return True
        else:
            return False

    def __ListFromListParam(self,inStr):
        if not self.__IsListParam(inStr):
            return None
        else:
            return re.split(r'\s*,\s*',re.match(r'^\[\s*(.+)\s*\]$',inStr).groups()[0])

    # Check validity of argument type
    def __IsParamType(self,inStr,type):
        rtrn = None

        # checking single parameters
        if type == 'File Name':
            rtrn = self.__IsStrValidFileName(inStr)
        elif type == 'Field Name':
            rtrn = self.__IsStrValidFieldName(inStr)
        elif type == 'Import Name':
            rtrn = self.__IsStrValidImportName(inStr)
        elif type == 'Function Name':
            rtrn = self.__IsStrValidFunctionName(inStr)
        elif type == 'Field Type Description':
            rtrn = self.__IsStrValidFldTypeDesc(inStr)
        elif type == 'Integer':
            rtrn = self.__IsStrValidInt(inStr)
        elif type == 'Positive Integer':
            rtrn = self.__IsStrValidInt(inStr) and int(inStr) > 0
        elif type == 'Float':
            rtrn = self.__IsStrValidFloat(inStr)
        elif type == 'Positive Float':
            rtrn = self.__IsStrValidFloat(inStr) and float(inStr) > 0
        elif type == 'Boolean':
            rtrn = self.__IsStrValidBoolean(inStr)
        elif type == 'Fuzzy Value':
            rtrn = self.__IsStrValidFloat(inStr) and float(inStr) >= -1.0 and float(inStr) <= 1.0
        elif type == 'Truest or Falsest':
            if self.__IsStrValidInt(inStr):
                if int(inStr) == -1 or int(inStr) == 1:
                    rtrn = True
            if (inStr == '-1' or
                inStr == '1' or
                re.match(r'^[Tt][Rr][Uu][Ee][Ss][Tt]$',inStr) or
                re.match(r'^[Ff][Aa][Ll][Ss][Ee][Ss][Tt]$',inStr)):
                rtrn = True
            else:
                rtrn = False

        # single level of recursion for List types
        elif type in [
            'File Name List',
            'Field Name List',
            'Import Name List',
            'Function Name List'
            'Integer List',
            'Positive Integer List',
            'Float List',
            'Positive Float List',
            'Boolean List',
            'Fuzzy Value List'
            ]:

            rtrn = True
            if not self.__IsListParam(inStr):
                rtrn = False
            else:
                for inStrToken in self.__ListFromListParam(inStr):
                    if not self.__IsParamType(inStrToken,re.match(r'(.*) List',type).groups()[0]):
                        rtrn = False
                        break
        else:
            raise Exception(
                '\n********************ERROR********************\n'+
                'Illegal parameter type: '+type)
        return rtrn
    # def __IsParamType(self,inStr,type):

    def GetCmdHelp(self):
        outStr = '%s Command\n\n'%(self.cmdDesc['Name'])
        outStr += '  Usage:\n\n'
        if 'Result' in list(self.cmdDesc.keys()):
            outStr += '    Result = %s(ParameterName = ParameterValue,...)\n\n'%(self.cmdDesc['Name'])
            outStr += '  where:\n\n'
            outStr += '    Result is a %s\n\n'%(self.cmdDesc['Result'])
        else:
            outStr += '    %s(ParameterName = ParameterValue,...)\n\n'%(self.cmdDesc['Name'])

        outStr += '    Required Parameters:\n\n'
        reqParams = list(self.cmdDesc['Required Params'].keys())
        if len(reqParams) == 0:
            outStr += '      None\n'
        else:
            for paramNm in reqParams:
                outStr += '      %s is a %s\n'%(paramNm,self.cmdDesc['Required Params'][paramNm])

        outStr += '\n    Optional Parameters:\n\n'
        optParams = list(self.cmdDesc['Optional Params'].keys())
        if len(optParams) == 0:
            outStr += '      None\n'
        else:
            for paramNm in optParams:
                outStr += '        %s is a %s\n'%(paramNm,self.cmdDesc['Optional Params'][paramNm])

        return outStr
    # def GetCmdHelp(self):

    # Parse rslt, command, and params out of command
    def __ParseEEMSCmd(self):

        if not self.cmdStr:
            raise Exception(
                '\n********************ERROR********************\n'+
                '__ParseEEMSCmd called on empty command string.')

        exprParse = re.match(r'\s*([^\s]+.*=){0,1}\s*([^\s]+.*)\s*\(\s*(.*)\s*\)',self.cmdStr)

        if not exprParse or len(exprParse.groups()) != 3:
            raise Exception(
                '\n********************ERROR********************\n'+
                'Invalid command format.\n'+
                'Full erroneous command is:\n'+
                '  %s\n'%(self.cmdStr)+
                'Proper command format is:\n'+
                '  Result = Command(Parameter1 = ParameterValue1,...)')

        self.parsedCmd = {}
        if exprParse.groups()[0] != None:
            self.parsedCmd['rslt'] = re.sub(r'\s*=\s*','',self.__TrimEndSpace(exprParse.groups()[0]))

        self.parsedCmd['cmd'] = self.__TrimEndSpace(exprParse.groups()[1])

        self.__InitCmdDesc()

        # Parse out the parameters
        paramStr = exprParse.groups()[2]
        paramPairs = []
        while paramStr != '':
            paramPairMatchObj = re.match(r'\s*([^=]*=\s*\[[^\[]*\])\s*,*\s*(.*)',paramStr)
            if paramPairMatchObj:
                paramPairs.append(paramPairMatchObj.groups()[0])
                paramStr = paramPairMatchObj.groups()[1]
            else:
                paramPairMatchObj = re.match(r'\s*([^=,]*=\s*[^,]*)\s*,*\s*(.*)',paramStr)
                if paramPairMatchObj:
                    paramPairs.append(paramPairMatchObj.groups()[0])
                    paramStr = paramPairMatchObj.groups()[1]
                else:
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'Illegal parameter specification at section *%s*\n'%(paramStr)+
                        'Full erroneous command is:\n'
                        '  %s\n'%(self.cmdStr)+
                        'Proper command format is:\n'+
                        '  Result = Command(Parameter1 = ParameterValue1,...)')

            # if paramPair:...else:

        # while paramStr != '':

        paramD = {}

        for paramPair in paramPairs:

            paramTokens = re.split(r'\s*=\s*',paramPair)

            paramTokens[0] = self.__TrimEndSpace(paramTokens[0])
            paramTokens[1] = self.__TrimEndSpace(paramTokens[1])

            paramTokens[1] = re.sub(r'\s*\[\s*','[',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*\]\s*',']',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*,\s*',',',paramTokens[1])

            if (len(paramTokens) != 2
                or paramTokens[0] == ''
                or paramTokens[1] == ''
                ):

                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Parameter specification error in *%s*\n'%(paramPair)+
                    'Full erroneous command is:\n'
                    '  %s\n'%(self.cmdStr)+
                    'Proper command format is:\n'+
                    '  Result = Command(Parameter1 = ParameterValue1,...)')

            # Adjustment to Truest or Falsest in SELECTEDUNION command.
            # previous valid values were 1 or -1, so these get corrected here
            if self.parsedCmd['cmd'] == 'SELECTEDUNION' and paramTokens[0] == 'TruestOrFalsest':
                if paramTokens[1] == '1' or paramTokens[1] == '+1':
                    paramTokens[1] = 'Truest'
                elif paramTokens[1] == '-1':
                    paramTokens[1] = 'Falsest'

            paramD[paramTokens[0]] = paramTokens[1]

        self.parsedCmd['params'] = paramD

        # for paramPair in paramPairs:
    # def __ParseEEMSCmd(self):

    # Check command and trigger Exception if it is not valid
    def __ValidateCmd(self):

        # Are the presence and format of Result valid?
        if 'Result' not in list(self.cmdDesc.keys()):
            if 'rslt' in list(self.parsedCmd.keys()):

                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Command does not use Result.\n'+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

        else:
            if not self.__IsParamType(self.parsedCmd['rslt'],self.cmdDesc['Result']):

                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Invalid Result specification in command:\n'+
                    '  *%s* must be valid %s\n:'%(
                        self.parsedCmd['rslt'],self.cmdDesc['Result'])+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())
        # if 'Result' not in self.cmdDesc['Required Params'].keys():...else:

        # Are there any parameters that don't belong?
        if self.parsedCmd['cmd'] not in ['CALLEXTERN']:
            for paramName in list(self.parsedCmd['params'].keys()):
                if paramName not in list(self.cmdDesc['Required Params'].keys())+list(self.cmdDesc['Optional Params'].keys()):
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'Invalid parameter for this command: *%s*\n'%(paramName)+
                        'Full erroneous command is:\n'+
                        '  %s\n'%(self.cmdStr)+
                        '\n\nCommand Help:\n\n'+
                        self.GetCmdHelp())

        # Are all the required parameters present?
        for paramName in self.cmdDesc['Required Params']:
            if paramName not in list(self.parsedCmd['params'].keys()):
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Required parameter missing from command: *%s*:\n'%(paramName)+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

        # Are all the parameter values legal?
        for paramName in list(self.parsedCmd['params'].keys()):

            if paramName in list(self.cmdDesc['Required Params'].keys()):
                paramType = self.cmdDesc['Required Params'][paramName]
            elif paramName in list(self.cmdDesc['Optional Params'].keys()):
                paramType = self.cmdDesc['Optional Params'][paramName]
            elif self.parsedCmd['cmd'] in ['CALLEXTERN']:
                paramType = 'skip'

            if paramType != 'skip':
                if not self.__IsParamType(self.parsedCmd['params'][paramName],paramType):
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'Invalid parameter value *%s = %s*:\n'%(
                            paramName,self.parsedCmd['params'][paramName])+
                        '  *%s* is not a valid value for parameter type: %s\n'%
                        (self.parsedCmd['params'][paramName],paramType)+
                        'Full erroneous command is:\n'+
                        '  %s\n'%(self.cmdStr)+
                        '\n\nCommand Help:\n\n'+
                        self.GetCmdHelp())

        # Are the other conditions for a correct command met?

        if self.parsedCmd['cmd'] in ['CVTTOFUZZYCURVE','CVTTOFUZZYCAT']:
            if (len(self.__ListFromListParam(self.parsedCmd['params']['RawValues'])) !=
                len(self.__ListFromListParam(self.parsedCmd['params']['FuzzyValues']))):
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Number of RawValues must be the same as the number of FuzzyValues.\n'+
                    '  Command has %d RawValues and %d FuzzyValues.\n'%(
                        len(self.__ListFromListParam(self.parsedCmd['params']['RawValues'])),
                        len(self.__ListFromListParam(self.parsedCmd['params']['FuzzyValues'])))+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

            rawVals = [float(x) for x in self.__ListFromListParam(self.parsedCmd['params']['RawValues'])]
            for ndx in range(0,len(rawVals)-1):
                if rawVals[ndx] in rawVals[ndx+1:]:
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'All RawValues must be unique.\n'+
                        '  RawValue %f appears more than once.\n'%(rawVals[ndx])+
                        'Full erroneous command is:\n'+
                        '  %s\n'%(self.cmdStr)+
                        '\n\nCommand Help:\n\n'+
                        self.GetCmdHelp())

        # if self.parsedCmd['cmd'] in ['CVTTOFUZZYCURVE','CVTTOFUZZYCAT']:

        if self.parsedCmd['cmd'] in ['WTDUNION','WTDMEAN','WTDSUM','WTDEMDSAND']:
            if (len(self.__ListFromListParam(self.parsedCmd['params']['InFieldNames'])) !=
                len(self.__ListFromListParam(self.parsedCmd['params']['Weights']))):
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Number of InFieldNames must be the same as the number of Weights.\n'+
                    '  Command has %d InFieldNames and %d Weights.\n'%(
                        len(self.__ListFromListParam(self.parsedCmd['params']['InFieldNames'])),
                        len(self.__ListFromListParam(self.parsedCmd['params']['Weights'])))+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

        if self.parsedCmd['cmd'] in ['SELECTEDUNION']:
            if (int(self.parsedCmd['params']['NumberToConsider']) >
                len(self.__ListFromListParam(self.parsedCmd['params']['InFieldNames']))):
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'NumberToConsider can not be greater than number of InFieldNames.\n'+
                    '  Number to consider is %s, number of FieldNames is %d.\n'%(
                        int(self.parsedCmd['params']['NumberToConsider']),
                        len(self.__ListFromListParam(self.parsedCmd['params']['InFieldNames'])))+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

        if self.parsedCmd['cmd'] in ['MEANTOMID']:
            if len(self.parsedCmd['params']['FuzzyValues'].split(',')) != 5:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Exactly 5 fuzzy values required.\n'+
                    'Full erroneous command is:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

    # def __ValidateCmd(self):

############################################################
# Public methods
############################################################

    def GetResultName(self):
        if self.HasResultName():
            return self.parsedCmd['rslt']
        else:
            raise Exception(
                '\n********************ERROR********************\n'+
                'Requested ResultName from command with no ResultName\n'+
                'Command without ResultName is:\n'+
                '  %s\n'%(self.cmdStr))

    def GetCommandName(self):
        return self.parsedCmd['cmd']

    def IsReadCmd(self):
        return self.parsedCmd['cmd'] in ['READ','READMULTI']

    def HasParam(self,paramNm):
        return paramNm in list(self.parsedCmd['params'].keys())

    def HasResultName(self):
        return 'rslt' in list(self.parsedCmd.keys())

    def IsRequiredParam(self,paramNm):
        return paramNm in list(self.cmdDesc['Required Params'].keys())

    def IsOptionalParam(self,paramNm):
        return paramNm in list(self.cmdDesc['Optional Params'].keys())

    def GetOptionalParamNames(self):
        return list(self.cmdDesc['Optional Params'].keys())

    def GetRequiredParamNames(self):
        return list(self.cmdDesc['Required Params'].keys())

    def GetRtrnType(self):
        return self.cmdDesc['RtrnType']

    def GetInputType(self):
        return self.cmdDesc['InputType']

    def GetReadableNm(self):
        return self.cmdDesc['ReadableNm']

    def GetShortDesc(self):
        return self.cmdDesc['ShortDesc']

    def GetParamType(self,paramNm):
        if self.IsRequiredParam(paramNm):
            return self.cmdDesc['Required Params'][paramNm]
        elif self.IsOptionalParam(paramNm):
            return self.cmdDesc['Optional Params'][paramNm]
        elif self.GetCommandName() == 'CALLEXTERN':
            return 'Unknown Type'
        else: # parameter not valid for this command
            raise Exception(
                '\n********************ERROR********************\n'+
                'Requested parameter *%s* invalid for this command.\n*'%paramNm+
                'Full command from which parameter was requested:\n'+
                '  %s\n'%(self.cmdStr)+
                '\n\nCommand Help:\n\n'+
                self.GetCmdHelp())

    def GetCommandString(self):
        return self.cmdStr

    def GetParamNames(self):
        return list(self.parsedCmd['params'].keys())

    # returns the parameter with the appropriate format (e.g. list of floats)
    def GetParam(self,paramNm):

        paramType = self.GetParamType(paramNm) # also checks for param validity

        try:
            paramVal = self.parsedCmd['params'][paramNm]
        except KeyError:
            if self.IsOptionalParam(paramNm):
                return None
            else:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Required parameter *%s* missing from command.\n*'%paramNm+
                    'Full command from which parameter was requested:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

        if paramType in ['File Name',
                         'Field Name',
                         'Truest or Falsest',
                         'Import Name',
                         'Function Name',
                         'Unknown Type'
                         ]:
            return paramVal

        elif paramType in ['Integer',
                         'Positive Integer']:
            return int(paramVal)

        elif paramType in ['Float',
                         'Positive Float',
                         'Fuzzy Value']:
            return float(paramVal)

        elif paramType in ['Boolean']:

            rtrn = None
            if (paramVal == '1' or
                re.match(r'^[Tt][Rr][Uu][Ee]$',paramVal)):
                rtrn = True
            elif (paramVal == '0' or
                  paramVal == '-1' or
                re.match(r'^[Ff][Aa][Ll][Ss][Ee]$',paramVal)):
                rtrn = False
            else:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Required parameter *%s* must be one of ["True","False","0","1"].\n*'%paramNm+
                    'Full command in which parameter is incorrect:\n'+
                    '  %s\n'%(self.cmdStr)+
                    '\n\nCommand Help:\n\n'+
                    self.GetCmdHelp())

            return bool(rtrn)

        elif paramType in ['Field Type Description']:
            return str(paramVal)

        elif paramType in ['File Name List',
                         'Field Name List']:
            return self.__ListFromListParam(paramVal)

        elif paramType in ['Integer List',
                         'Positive Integer List']:
            return [int(x) for x in self.__ListFromListParam(paramVal)]

        elif paramType in ['Float List',
                         'Positive Float List',
                         'Fuzzy Value List']:
            return [float(x) for x in self.__ListFromListParam(paramVal)]

        else: # Unkown parameter type
            raise Exception(
                '\n********************ERROR********************\n'+
                'Unknown parameter type *%s* for this command.\n*'%paramType+
                'Full command from which parameter was requested:\n'+
                '  %s\n'%(self.cmdStr)+
                '\n\nCommand Help:\n\n'+
                self.GetCmdHelp())

    # def GetParam(self,paramNm):

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        return self
    # def __exit__(self,exc_type,exc_value,traceback):

# class EEMSCmd(object):
######################################################################

######################################################################
# The EEMSProgram class manages a program written in EEMS
######################################################################
#
# The idea is that a user produces an EEMS program file. Simply a file
# of related commands in the EEMS language. The EEMSProgram class
# reads these commands one by one, creating an EEMSCommand object for
# each one. (EEMSCommand parses the user's EEMS command, and does
# extensive error checking on it).
#
# Once it has read all the commands, EEMSProgram examines the commands
# to produce an execution order that honors the dependencies among the
# EEMSCommands. If an EEMSCommand depends on a value not either read
# into or produced by one of the other EEMSCommands, an Exception is
# raised. If there is circular logic in the dependencies of the
# EEMSCommands, this condition is detected and an Exception is raised.
#
# EEMSCommands are stored in cmds{}, a dictionary keyed by the rslt
# field of an entry's EEMSCommand. The order of commands is maintained
# in the list orderedCmds[]. Each entry in orderedCmds is one of the
# unique keys in cmds. A current command is maintained by the
# crntCmdNdx, the index of one of the items in orderedCmds[].
#
# After instantiation of an EEMSCommand object, all EEMSCommands are
# assumed to be syntactically correct, the order of execution
# is set, and the current command is set to the first command in
# the ordered execution.
#
# The user can then increment or decrement the current command and
# has access to all data within the current command.
#
# Method History
#
# 2013 - tjs
#
# This was originally implemented as part of EEMS for Arc.
#
# 2014.01.29 - tjs
#
# Updating as part of update of EEMS language and to use the EEMSCmd
# class which provides an abstraction of EEMS commands and offloads
# the parsing and error checking of a user's EEMS commands.
#
# 2015.01.16 - tjs
#
# Rewrote __init__ to allow for EEMS commands to spread over more
# than one line and to give explanatory error messages on exception
#
######################################################################

class EEMSProgram(object):

    def __init__(self, fNm):
        # Parse the EEMS command file. Each command must start on a
        # new line.

        self.unorderedCmds = [] # commands in no particular order
        self.orderedCmds = [] # commands in order of execution
        self.crntCmdNdx = None # The index of the current command in orderedCmds
        self.allDefinedFieldNms = {} # unordered fields defined by by EEMS commands

        cmdLine = ''      # buffer to build command from lines of input file
        inParens = False  # whether or not parsing is within parentheses
        parenCnt = 0      # count of parenthesis levels
        inLineCnt = 0     # line number of input file for error messages.

        if isinstance(fNm, str):
            fObj = open(fNm, 'rU')
        else:
            fObj = fNm

        with fObj as inFile:
            for inLine in inFile:
                inLineCnt +=1
                if cmdLine == '':
                    cmdStartLine = inLine
                    cmdStartLineNum = inLineCnt
                tmpLine = re.sub('#.*$','',inLine)
                tmpLine = tmpLine.strip()

                for charNdx in range(len(tmpLine)):
                    cmdLine += tmpLine[charNdx]
                    if tmpLine[charNdx] == '(':
                        inParens = True
                        parenCnt += 1
                    elif tmpLine[charNdx] == ')':
                        parenCnt -= 1

                    if parenCnt < 0:
                        raise Exception(
                            '\n********************ERROR********************\n'+
                            'Unmatched right paren *)*\n'+
                            '  file: {}, line {}:\n'.format(fObj.name,inLineCnt)+
                            '  {}\n'.format(inLine)
                            )
                    elif inParens and parenCnt == 0:
                        if charNdx < (len(tmpLine)-1):
                            raise Exception(
                                '\n********************ERROR********************\n'+
                                'Extraneous characters beyond end of command\n' +
                                '  file: {}, line {}:\n'.format(fObj.name,inLineCnt) +
                                '  {}\n'.format(inLine)
                            )
                        else:
                            self.__AddCmd(cmdLine)
                            cmdLine = ''
                            inParens = False
                            parenCnt = 0

                        # if charNdx < (len(tmpLine)-1):
                    # if parenCnt < 0:...elif...
                # for charNdx in range(len(tmpLine)):
            # for inLine in inFile:
        # with fObj as inFile:

        # EEMS command file has been parsed.

        if parenCnt > 0:
            # Raise exception if there was an unmatched left paren
            raise Exception(
                '\n********************ERROR********************\n'+
                'Unmatched {} left parens *(*\n'.format(parenCnt) +
                '  file: {}, command starting on line {}:\n'.format(fNm,cmdStartLineNum) +
                '  {}\n'.format(cmdStartLine)
                )

        if len(self.unorderedCmds) == 0:
            # Raise exception if EEMS command file had no commands.
            raise Exception(
                '\n********************ERROR********************\n'+
                'EEMS command file has no commands.\n'+
                '  file: {}\n'.format(fNm)
                )

        self.__OrderCmds()
    # def GetNodesFromFile(self, fNm):

    def __enter__(self):
        return self
    # def __enter__(self):

    def __GetReadFieldNms(self,cmd):
        if cmd.GetCommandName() in ['READ']:
            if cmd.HasParam('NewFieldName'):
                return [cmd.GetParam('NewFieldName')]
            else:
                return [cmd.GetParam('InFieldName')]
        elif cmd.GetCommandName() in ['READMULTI']:
            if cmd.HasParam('NewFieldNames'):
                return cmd.GetParam('NewFieldNames')
            else:
                return cmd.GetParam('InFieldNames')
        else:
            raise Exception(
                'Programming Error, __GetReadFieldNms() for READ type EEMSCmds only.\n'+
                '  EEMSCmd string for command passed to this method:'+
                '    %s'%cmd.GetCommandString())
    # def __GetReadFieldNms(self,cmd):

    def __GetDependFieldNms(self,cmd):
        if cmd.IsReadCmd():
            return []
        if cmd.HasParam('InFieldNames'):
            return cmd.GetParam('InFieldNames')
        elif cmd.HasParam('InFieldName'):
            return [cmd.GetParam('InFieldName')]
        elif cmd.GetCommandName() == 'DIF':
            return [
                cmd.GetParam('StartingFieldName'),
                cmd.GetParam('ToSubtractFieldName')
                ]
        else:
            raise Exception(
                'Programming Error!\n'+
                '  Command has neither InFieldNames nor InFieldName.\n'+
                '  Command string:\n'+
                '    %s'%cmd.GetCommandString())
    # def __GetDependFieldNms(self,cmd):

    def __AddCmd(self,cmdStr):
        cmd = EEMSCmd(cmdStr)

        if cmd.HasResultName():
            rsltNm = cmd.GetResultName()
            if rsltNm in list(self.allDefinedFieldNms.keys()):
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'A field is defined by two different commands.\n'+
                    'Commands with duplicate definitions:\n'+
                    '  %s\n'%cmdStr+
                    '  %s\n'%self.allDefinedFieldNms[rsltNm].GetCommandString())
            else:
                self.allDefinedFieldNms[rsltNm] = cmd

        elif cmd.IsReadCmd():

            for fldNm in self.__GetReadFieldNms(cmd):
                if fldNm in list(self.allDefinedFieldNms.keys()):
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'A field is defined more than once.\n'+
                        'Commands with repeated definitions:\n'+
                        '  %s\n'%cmdStr+
                        '  %s\n'%self.allDefinedFieldNms[fldNm].GetCommandString())

                else:
                    self.allDefinedFieldNms[fldNm] = cmd

        # if cmd.HasResultName():

        self.unorderedCmds.append(cmd)

    # def __AddCmd(self,cmdStr):

    def __OrderCmds(self):

        # Orders the commands for execution.
        # First checks for missing ResultNames in dependencies
        # Then orders nodes and while doing so, detects
        # circular logic in commands and commands whose dependent
        # fields are undefined

        # check for a missing dependency
        for cmd in self.unorderedCmds:
            for dependNm in self.__GetDependFieldNms(cmd):
                if dependNm not in list(self.allDefinedFieldNms.keys()):
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'Command depends on undefined field *%s*\n'%dependNm+
                        'Full command with error:\n'
                        '  %s\n'%cmd.GetCommandString())
        # for rsltNm in self.unorderedCmds

        # order the fields for execution

        self.orderedCmds = [] # list of command ResultNames in execution order
        dpndsInOrderedCmds = []

        while len(self.unorderedCmds) > 0:
            startingCmdsToBeOrderedLen = len(self.unorderedCmds)

            # Step backwards through cmdsToBeOrdered so that popping
            # elements does not interfere with indexing

            ndxs = list(range(len(self.unorderedCmds)))
            ndxs.reverse()

            for ndx in ndxs:
                cmd = self.unorderedCmds[ndx]

                if cmd.IsReadCmd(): # need InField(s) not ResultName
                    # Move command from unordered to order, grab the
                    # field(s) it defines and loop
                    self.orderedCmds.append(cmd)
                    self.unorderedCmds.pop(ndx)
                    dpndsInOrderedCmds += self.__GetReadFieldNms(cmd)
                    continue

                else:

                    # check if all the fields the current field depends on are
                    # defined by commanes in the the orderedCmds list

                    cmdHasAllDepends = True

                    for dependFldNm in self.__GetDependFieldNms(cmd):
                            if dependFldNm not in dpndsInOrderedCmds:
                                cmdHasAllDepends = False
                                break
                    # for dependFldNm in self.__GetDependFieldNms(rsltFldNm):
                # if rsltFldNm in ['READ']: # No dependency

                if cmdHasAllDepends:
                    self.orderedCmds.append(cmd)
                    self.unorderedCmds.pop(ndx)
                    dpndsInOrderedCmds.append(cmd.GetResultName())
                # if fldIsIndependent:

            # for ndx in ndxs:

            # if no independent fields were found, then there is
            # a dependency cycle in the structure of the commands

            if startingCmdsToBeOrderedLen == len(self.unorderedCmds):
                cmdStrings = ''
                for cmd in self.unorderedCmds:
                    cmdStrings += '  '+cmd.GetCommandString()+'\n'
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Circular logic in the dependencies for this subset of commands:'+
                    cmdStrings)

        # while len(nodesToBeOrdered) > 0:
        self.crntCmdNdx = 0
    # def __OrderCmds(self):

    def __ParseDict(self,nodeFld,treeImage, lvl):
    # parses the dictionary into a dependency tree

        treeImage.append((nodeFld,lvl))
        lvl = lvl + 1

        if not self.allDefinedFieldNms[nodeFld].IsReadCmd():
            for subFld in self.__GetDependFieldNms(self.allDefinedFieldNms[nodeFld]):
                self.__ParseDict(subFld, treeImage,lvl)

        return treeImage

    # def __ParseDict(self,nodeFld,treeImage, lvl)

############################################################
# Public methods
############################################################

    def NextCmd(self):
        self.crntCmdNdx += 1
        if self.crntCmdNdx >= len(self.orderedCmds):
            self.crntCmdNdx = None
            return False
        else:
            return True

    def PrevCmd(self):
        self.crntCmdNdx -= 1
        if self.crntCmdNdx < 0:
            self.crntCmdNdx = None
            return False
        else:
            return True

    def GetCrntCmd(self):
        return self.orderedCmds[self.crntCmdNdx]

    def SetCrntCmdToFirst(self):
        self.crntCmdNdx = 0

    def IsCrntRequiredParam(self,paramNm):
        return self.orderedCmds[self.crntCmdNdx].IsRequiredParam(paramNm)

    def IsCrntOptionalParam(self,paramNm):
        return self.orderedCmds[self.crntCmdNdx].IsOptionalParam(paramNm)

    def CrntHasParam(self,paramNm):
        return self.orderedCmds[self.crntCmdNdx].HasParam(paramNm)

    def GetAllResultNames(self):
        rtrnLst = []
        for cmd in self.cmds:
            if cmd.HasResultName(): rtrnLst += cmd.GetResultName()
        return rtrnLst

    def GetCrntResultName(self):
        return self.orderedCmds[self.crntCmdNdx].GetResultName()

    def GetCrntCmdName(self):
        return self.orderedCmds[self.crntCmdNdx].GetCommandName()

    def GetParamTypeFromCrntCmd(self,paramNm):
        return self.orderedCmds[self.crntCmdNdx].GetParamType(paramNm)

    def GetParamFromCrntCmd(self,paramNm):
        return self.orderedCmds[self.crntCmdNdx].GetParam(paramNm)

    def GetCrntCmdString(self):
        return self.orderedCmds[self.crntCmdNdx].GetCommandString()

    def GetParamNmsFromCrntCmd(self):
        return self.orderedCmds[self.crntCmdNdx].GetParamNames()

    def GetOptionalParamNmsForCrntCmd(self):
        return self.orderedCmds[self.crntCmdNdx].GetOptionalParamNames()

    def GetRequiredParamNmsForCrntCmd(self):
        return self.orderedCmds[self.crntCmdNdx].GetRequiredParamNames()

    def GetCmdTree(self):
        # find the top node(s)

        depends = []
        for cmd in self.orderedCmds:
            if not cmd.IsReadCmd():
                depends = depends + self.__GetDependFieldNms(cmd)

        topNodeFlds = []
        for cmd in self.orderedCmds:
            if not cmd.IsReadCmd():
                if cmd.GetResultName() not in depends:
                    topNodeFlds.append(cmd.GetResultName())

        # order nodes by dependency, tracking depth

        treeImage = []
        for topNodeFld in topNodeFlds:
            self.__ParseDict(topNodeFld,treeImage,0)

        # return list

        return treeImage
    # def GetCmdTree(self):

    def GetCmdTreeAsString(self):
        rtrnStr = ''
        for fldTuple in self.GetCmdTree():
            rtrnStr += fldTuple[1] * '  |' + self.allDefinedFieldNms[fldTuple[0]].GetCommandString()+'\n'
        return rtrnStr

    # def GetCmdTreeAsString(self);

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        return self
    # def __exit__(self,exc_type,exc_value,traceback):

# class EEMSProgram(object):
######################################################################


######################################################################
# EEMSCmdRunnerBase class
######################################################################
# This class does the reading, computation and writing of EEMS data.
# It works in conjuction with the EEMSInterpreter class, which
# executes commands for this class.
#
# Commands for reading and writing are stubbed out in this class, as
# those are unique to data formats. To create a working version of
# EEMS, a child of this class must overload the reading and writing,
# and additional overloading may be necessary.
#
# Method History
#
# 2013 - tjs
#
# This was originally implemented as part of EEMS for Arc.
#
# 2014.01.29 - tjs
#
# Updating as part of update of EEMS language and framework
#
# 2014.02.10 - tjs
#
# Tested on CSV version of EEMS
######################################################################

class EEMSCmdRunnerBase(object):

########################################################################
# for control, etc
    MinForFuzzyLimit = -9999
    MaxForFuzzyLimit = 9999
########################################################################

    def __init__(self):
        self.EEMSFlds = {}
        self.outFileDict = {}
        self.arrayShape = None
    # def __init__(self):

    def __enter__(self):
        return self
    # def __enter__(self):

    def _WriteFldsToFiles(self):
        pass
    # def _WriteFldsToFile(self):

    def _CreateOutFileMap(self):
        # Create a map of files and fields
        outFileMap = {}

        outFldLst = list(self.EEMSFlds.keys())
        outFldLst.sort()
        for EEMSFldNm in outFldLst:
            crntOutFNm = self.EEMSFlds[EEMSFldNm]['outFNm']
            if crntOutFNm in list(outFileMap.keys()):
                outFileMap[crntOutFNm].append(EEMSFldNm)
            else:
                outFileMap[crntOutFNm] = [EEMSFldNm]
        # for EEMSFldNm in self.EEMSFlds.keys():
        return outFileMap
    # def _CreateOutFileMap(self):

    def _AddFieldToEEMSFlds(self,outFNm,fldNm,fldArray):
        if fldNm in list(self.EEMSFlds.keys()):
            raise Exception(
                '\n********************ERROR********************\n'+
                'Duplicated field name: *s*\n'%fldNm)

        if self.arrayShape == None:
            self.arrayShape = fldArray.shape
        else:
            if fldArray.shape != self.arrayShape:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Data Shape mismatch:\n'+
                    '  Field *%s* has shape %s, does not match %s.\n'%
                    (fldNm,fldArray.shape,self.arrayShape))

        if not isinstance(fldArray,np.ma.masked_array):
            fldArray = np.ma.masked_array(fldArray,mask=False)

        self.EEMSFlds[fldNm] = {'outFNm':outFNm,'data':fldArray}
    # def _AddFieldToEEMSFlds(self,outFNm,fldNm,fldArray):

    def _VerifyFuzzyField(self,inFldNm):
        if (self.EEMSFlds[inFldNm]['data'].min() < -1.0 or
            self.EEMSFlds[inFldNm]['data'].max() > 1.0):
            raise Exception(
                '\n********************ERROR********************\n'+
                'Field in fuzzy operation has range outside of fuzzy limits (-1,+1):\n'
                '  Field *%s* has range (%f,%f).\n'%
                (inFldNm,
                 self.EEMSFlds[inFldNm]['data'].min(),
                 self.EEMSFlds[inFldNm]['data'].max()))
    # def _VerifyFuzzyField(self,inFldNm):

    def _LinearCvtArray(
        self,
        srcArr,
        x1,
        y1,
        x2,
        y2):

        if x1 == x2:
            raise Exception(
                '\n********************ERROR********************\n'+
                '_LinearCvt requires x1 != x2.'+
                '  Values provided x1 = %f, x2 = %f, y1 = %f, y2 = %f\n'%(
                    x1,x2,y1,y2))

        m = (y2 - y1) / (x2 - x1)
        b = -m * x1 + y1

        return srcArr *m + b

    # def _LinearCvtArray(

########################################################################
# Public methods
########################################################################

    def Read(
        self,
        inFileName,
        inFieldName,
        outFileName,
        newFieldName
        ):
        if newFieldName != 'NONE':
            newFieldName = [newFieldName]

        self.ReadMulti(inFileName,[inFieldName],outFileName,newFieldName)
    # def Read(

    def ReadMulti(
        self,
        inFileName,
        inFieldNames,
        outFileName
        ):

        ##### This method should be overridden by a method in the
        ##### specific version of EEMS.

        pass

        # Confirm all inFieldNames in input file

        # determine inFieldNames col ndxs in input file

        # Add fields to EEMSFlds

    # def ReadMulti(...)

    def CvtToFuzzy(
        self,
        inFieldName,
        trueThreshold,
        falseThreshold,
        outFileName,
        rsltName
        ):

        if falseThreshold == self.MinForFuzzyLimit:
            falseThresh = self.EEMSFlds[inFieldName]['data'].min()
        elif falseThreshold == self.MaxForFuzzyLimit:
            falseThresh = self.EEMSFlds[inFieldName]['data'].max()
        else:
            falseThresh = falseThreshold

        if trueThreshold == self.MinForFuzzyLimit:
            trueThresh = self.EEMSFlds[inFieldName]['data'].min()
        elif trueThreshold == self.MaxForFuzzyLimit:
            trueThresh = self.EEMSFlds[inFieldName]['data'].max()
        else:
            trueThresh = trueThreshold

        if trueThresh == falseThresh:
            raise Exception(
                '\n********************ERROR********************\n'+
                'CvtToFuzzy(): trueThresh cannot equal falseThresh.\n'+
                '  trueThresh == falshThresh == *%f*'%trueThresh +
                'Arguments to this method call were:\n'+
                '  inFieldName:    %s\n'%inFieldName+
                '  trueThreshold:  %f\n'%trueThreshold+
                '  falseThreshold: %f\n'%falseThreshold+
                '  outFileName:    %s\n'%outFileName+
                '  rsltName:       %s\n\n'%rsltName+
                'Note that this can happen when using default values for\n'+
                'for true and false thresholds with an field that has a \n'+
                'uniform value\n')

        m = (-1 - 1) / (falseThresh - trueThresh)
        b = 1 -m * trueThresh

        newData = self.EEMSFlds[inFieldName]['data'] * m + b

        # take care of values outside of thresholds
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def CvtToFuzzy(...)

    def CvtToFuzzyCurve(
        self,
        inFieldName,
        rawValues,
        fuzzyValues,
        outFileName,
        rsltName
        ):

        # have to go in segments and apply linear to segment.
        # beyond x vals gets boundary y val
        # assumes sorted Raw and Fuzzy values

        newData = np.ma.where(
            self.EEMSFlds[inFieldName]['data'] != self.EEMSFlds[inFieldName]['data'],
            float('nan'),
            -9999
            )

        # values lower than lowest raw value
        newData = np.ma.where(self.EEMSFlds[inFieldName]['data'] <= rawValues[0], fuzzyValues[0], newData)

        for ndx in range(1,len(rawValues)):

            m = (fuzzyValues[ndx] - fuzzyValues[ndx-1]) / (rawValues[ndx] - rawValues[ndx-1])
            b = fuzzyValues[ndx-1] -m * rawValues[ndx-1]

            newData = np.ma.where(
                self.EEMSFlds[inFieldName]['data'] <= rawValues[ndx-1],
                newData,
                np.ma.where(
                    self.EEMSFlds[inFieldName]['data'] <= rawValues[ndx],
                    self.EEMSFlds[inFieldName]['data'] * m + b,
                    newData
                    )
                )

        # for ndx in range(1,len(rawValues)):

        # values greater than greatest raw value
        newData = np.ma.where(self.EEMSFlds[inFieldName]['data'] > rawValues[-1], fuzzyValues[-1], newData)

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def CvtToFuzzyCurve(...)

    def CvtToFuzzyCat(
        self,
        inFieldName,
        rawValues,
        fuzzyValues,
        defaultFuzzyValue,
        outFileName,
        rsltName
        ):

        newData = np.ma.zeros(self.EEMSFlds[inFieldName]['data'].shape)
        newData[:] = np.ma.where(
            self.EEMSFlds[inFieldName]['data'] != self.EEMSFlds[inFieldName]['data'], # nan check
            float('nan'),
            defaultFuzzyValue
            )

        for ndx in range(len(rawValues)):
            newData = np.ma.where(
                self.EEMSFlds[inFieldName]['data'] == rawValues[ndx],
                fuzzyValues[ndx],
                newData)

        # for ndx in range(len(rawValues)):

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def CvtToFuzzyCat(...)

    def CopyField(
        self,
        inFieldName,
        outFileName,
        rsltName
        ):
        self._AddFieldToEEMSFlds(outFileName,rsltName,self.EEMSFlds[inFieldName]['data'].copy())

    # def CopyField(...)

    def DifFlds(
        self,
        startingFieldName,
        toSubtractFieldName,
        outFileName,
        rsltName
        ):

        newData = (self.EEMSFlds[startingFieldName]['data'].copy() -
                   self.EEMSFlds[toSubtractFieldName]['data'].copy())
        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def DifFlds(...)

    def MinFlds(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        newData = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        for ndx in range(1,len(inFieldNames)):
            newData = np.ma.minimum(newData,self.EEMSFlds[inFieldNames[ndx]]['data'])

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def MinFlds(...)

    def MaxFlds(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        newData = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        for ndx in range(1,len(inFieldNames)):
            newData = np.ma.maximum(newData,self.EEMSFlds[inFieldNames[ndx]]['data'])

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def MaxFlds(...)

    def SumFlds(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        newData = np.ma.zeros(self.arrayShape)
        for inFldNm in inFieldNames:
            newData += self.EEMSFlds[inFldNm]['data']
        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def SumFlds(...)

    def MeanFlds(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        newData = np.ma.zeros(self.arrayShape)
        for inFldNm in inFieldNames:
            newData += self.EEMSFlds[inFldNm]['data']
        newData /= len(inFieldNames)
        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def MeanFlds(...)

    # Fuzzy logic operators (unless otherwise noted EMDS based)

    def FuzzyNot(
        self,
        inFieldName,
        outFileName,
        rsltName
        ):

        self._VerifyFuzzyField(inFieldName)
        newData = -1.0*(self.EEMSFlds[inFieldName]['data'].copy())

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyNot(...)

    def FuzzyUnion(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        newData = np.ma.zeros(self.arrayShape)
        for inFldNm in inFieldNames:
            newData += self.EEMSFlds[inFldNm]['data']
        newData /= float(len(inFieldNames))

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyUnion(...)

    def FuzzyOr(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        newData = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        for ndx in range(1,len(inFieldNames)):
            newData = np.ma.maximum(newData,self.EEMSFlds[inFieldNames[ndx]]['data'])

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyOr(...)

    def FuzzyAnd(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        newData = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        for ndx in range(1,len(inFieldNames)):
            newData = np.ma.minimum(newData,self.EEMSFlds[inFieldNames[ndx]]['data'])

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyAnd(...)

    def FuzzyEMDSAnd(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        minVals = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        meanVals = self.EEMSFlds[inFieldNames[0]]['data'].copy()

        for ndx in range(1,len(inFieldNames)):
            minVals = np.ma.minimum(minVals,self.EEMSFlds[inFieldNames[ndx]]['data'])
            meanVals += self.EEMSFlds[inFieldNames[ndx]]['data']

        meanVals /= len(inFieldNames)

        newData = minVals + (meanVals - minVals) * (minVals + 1) / 2

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyEMDSAnd(...)

    def FuzzyOrNeg(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        print('FuzzyOrNeg has been deprecated. Use FuzzyAnd instead')

        self.FuzzyAnd(
            inFieldNames,
            outFileName,
            rsltName
            )

    # def FuzzyOrNeg(...)

    def FuzzyWeightedUnion(
        self,
        inFieldNames,
        weights,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        newData = np.ma.zeros(self.arrayShape)

        for ndx in range(len(inFieldNames)):
            newData += self.EEMSFlds[inFieldNames[ndx]]['data'] * weights[ndx]
        newData /= sum(weights)

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyWeightedUnion(...)

    def FuzzyEMDSWeighteddAnd(
        self,
        inFieldNames,
        weights,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        minVals = self.EEMSFlds[inFieldNames[0]]['data'].copy()
        meanVals = self.EEMSFlds[inFieldNames[0]]['data'].copy() * weights[0]

        for ndx in range(1,len(inFieldNames)):
            minVals = np.ma.minimum(minVals,self.EEMSFlds[inFieldNames[ndx]]['data'])
            meanVals += self.EEMSFlds[inFieldNames[ndx]]['data'] * weights[ndx]

        meanVals /= sum(weights)

        newData = minVals + (meanVals - minVals) * (minVals + 1) / 2

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyEMDSWeightedAnd(...)

    def WeightedMean(
        self,
        inFieldNames,
        weights,
        outFileName,
        rsltName
        ):

        newData = np.ma.zeros(self.arrayShape)

        for ndx in range(len(inFieldNames)):
            newData += self.EEMSFlds[inFieldNames[ndx]]['data'] * weights[ndx]
        newData /= sum(weights)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def WeightedMean(...)

    def WeightedSum(
        self,
        inFieldNames,
        weights,
        outFileName,
        rsltName
        ):

        newData = np.ma.zeros(self.arrayShape)

        for ndx in range(len(inFieldNames)):
            newData += self.EEMSFlds[inFieldNames[ndx]]['data'] * weights[ndx]

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def WeightedSum(...)

    def FuzzySelectedUnion(
        self,
        inFieldNames,
        truestOrFalsest,
        numberToConsider,
        outFileName,
        rsltName
        ):

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        # if it's just one input field, just copy
        if len(inFieldNames) == 1:
            self.CopyField(inFieldNames[0],outFileName,rsltName)
        else:

            # combine and sort data for inFieldNames
            exec('stackedArrs = np.ma.concatenate(([self.EEMSFlds[\''+ \
                '\'][\'data\']],[self.EEMSFlds[\''.join(inFieldNames)+ \
                '\'][\'data\']]))')

            stackedArrs.sort(axis=0, kind='heapsort')

            # range to consider
            if re.match(r'^[Tt][Rr][Uu][Ee][Ss][Tt]$',truestOrFalsest):
                # Truest pulls from the high end of the sorted array
                myRange = list(range(len(inFieldNames)-numberToConsider,len(inFieldNames)))
            elif re.match(r'^[Ff][Aa][Ll][Ss][Ee][Ss][Tt]$',truestOrFalsest):
                # Falsest pulls from the low end of the array
                myRange = list(range(numberToConsider))
            else:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Selected Union truestOrFalsest must be either *Truest* or *Falsest*.\n'+
                    '  Value was: *%s*\n'%truestOrFalsest)

            newData = stackedArrs[myRange].mean(axis=0)
            del(stackedArrs)

            # insure that rounding errors don't accumulate
            newData = np.ma.where(newData > 1.0, 1.0, newData)
            newData = np.ma.where(newData < -1.0, -1.0, newData)

            self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzySelectedUnion(...)

    def FuzzyXOr(
        self,
        inFieldNames,
        outFileName,
        rsltName
        ):

        # formula is:
        # Truest - (Truest - 2nd Truest) * (2nd Truest - full False)/(Truest - full False)

        if len(inFieldNames) < 2:
            raise Exception(
                '\n********************ERROR********************\n'+
                'FuzzyXOr takes a minimum of 2 inFieldNames.\n'
                '  rsltName: *%s*, inFieldNames: *%s*\n'%(rsltName,inFieldNames[0]))

        # Get the two truest...
        # compute the difference in their fuzzy values...
        # normalize the result over fuzzy space.

        for inFldNm in inFieldNames:
            self._VerifyFuzzyField(inFldNm)

        # combine and sort data for inFieldNames
        exec('stackedArrs = np.ma.concatenate(([self.EEMSFlds[\''+ '\'][\'data\']],[self.EEMSFlds[\''.join(inFieldNames)+'\'][\'data\']]))')

        stackedArrs.sort(axis=0, kind='heapsort')

        newData = np.ma.where(
            stackedArrs[-1] != -1,
            stackedArrs[-1] - \
                (stackedArrs[-1] - stackedArrs[-2]) * \
                (stackedArrs[-2] - -1) / \
                (stackedArrs[-1] - -1),
            -1)

        del(stackedArrs)

        # insure that rounding errors don't accumulate
        newData = np.ma.where(newData > 1.0, 1.0, newData)
        newData = np.ma.where(newData < -1.0, -1.0, newData)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def FuzzyXOr(...)

    # Begin TWS Tools

    # TWS 4.3
    def ScoreRangeBenefit(
            self,
            inFieldName,
            outFileName,
            rsltName
            ):

        minValue=np.amin(self.EEMSFlds[inFieldName]['data'])
        maxValue=np.amax(self.EEMSFlds[inFieldName]['data'])

        newData = (self.EEMSFlds[inFieldName]['data'] - minValue) / (maxValue - minValue)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def ScoreRangeBenefit(...)

    # TWS 4.4
    def ScoreRangeCost(
            self,
            inFieldName,
            outFileName,
            rsltName
            ):

        minValue=np.amin(self.EEMSFlds[inFieldName]['data'])
        maxValue=np.amax(self.EEMSFlds[inFieldName]['data'])

        newData = (maxValue - self.EEMSFlds[inFieldName]['data']) / (maxValue - minValue)

        self._AddFieldToEEMSFlds(outFileName,rsltName,newData)

    # def ScoreRangeCost(...)

    # TWS C&D
    def MeanToMid(
            self,
            inFieldName,
            ignoreZeros,
            fuzzyValues,
            outFileName,
            rsltName
            ):

        # If the ignoreZeros flag is enabled, create an array from the input data without 0's
        # for computing the 3 means.

        if ignoreZeros:
            # This should give us a 1D array with zeros gone
            valArr = self.EEMSFlds[inFieldName]['data'][self.EEMSFlds[inFieldName]['data'] != 0]
        else:
            valArr = cp.deepcopy(self.EEMSFlds[inFieldName]['data'].ravel())

        # Note there is a bug with nd.ma.mean() that causes it to return a masked array
        # if the mask is False, but a float if the mask is a list. Thus, we must
        # test the result of the mean() operation and make it a float if it is not a
        # float already.

        meanVal = valArr.mean()
        if isinstance(meanVal,np.ndarray): meanVal = meanVal[0]

        # Endvals and means of bisected array
        lowVal = valArr.min()
        if isinstance(lowVal,np.ndarray): lowVal = lowVal[0]

        lowMeanVal = valArr[valArr < meanVal].mean()
        if isinstance(lowMeanVal,np.ndarray): lowMeanVal = lowMeanVal[0]

        hiVal = valArr.max()
        if isinstance(hiVal,np.ndarray): hiVal = hiVal[0]

        hiMeanVal = valArr[valArr > meanVal].mean()
        if isinstance(hiMeanVal,np.ndarray): hiMeanVal = hiMeanVal[0]

        # Call the CvtToFuzzyCurve method to perform the interpolation.
        self.CvtToFuzzyCurve(
            inFieldName,
            [lowVal, lowMeanVal, meanVal, hiMeanVal, hiVal],
            fuzzyValues,
            outFileName,
            rsltName
            )

    # def MeanToMid(...)

    def CallExtern(self):
        raise Exception(
            '\n********************ERROR********************\n'+
            'CALLEXTERN is not implemented!\n'
            )

    # def CallExtern(self):

    def Finish(self):
        # self._WriteFldsToFiles()
        pass

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        return self
    # def __exit__(self,exc_type,exc_value,traceback):

# class EEMSCmdRunnerBase(object):
######################################################################

######################################################################
# EEMSInterpreter
######################################################################
#
# This class sits between a user-generated EEMS program and an
# EEMSCmdRunner. The constructor takes a file name for the user-
# generated EEMS program and an EEMSCmdRunner as arguments.
#
# With the passed-in user program file, it creates an EEMSProgram
# object. It then pulls commands from the EEMSProgram object, and
# interprets them for execution in the EEMSCmdRunner.
#
# Note that there are some options for overriding parameters that
# come from the EEMSProgram object. These are here in order to force
# direct the use of input and output files under the Arc implementation
# of EEMS. These should be used with caution.
#
# This class may be used as is, but is called Base, as extension of it
# may prove valuable.
# Revision History
#
# 2014.02.01 - tjs
#
# Completed writing of this class.
#
######################################################################

class EEMSInterpreter(object):

    def __init__(self,EEMSProgFNm,cmdRunner,verbose=False):
        self.myProg = None # EEMSProgram object
        self.myCmdRunner = cmdRunner
        self.verbose = verbose

        # default values for optional params without values
        self.dfltOptnlParamVals = {}

        # values to override required params. Be careful!
        self.paramOverrideVals = {}

        self.myProg = EEMSProgram(EEMSProgFNm)
        self.myProg.SetCrntCmdToFirst() # start at beginning

    def __enter__(self):
        return self
    # def __enter__(self):

    def SetVerbose(self,TorF):
        self.verbose = TorF

    def SetDfltOptionalParam(self,paramNm,paramVal):
            self.dfltOptnlParamVals[paramNm] = paramVal

    def SetOverrideParam(self,paramNm,paramVal):
            self.paramOverrideVals[paramNm] = paramVal

    def RunProgram(self):

        if self.verbose: print('Running Commands:')

        while True: # work loop over all commands

            if self.verbose:
                print('  '+self.myProg.GetCrntCmdString())

            cmdNm = self.myProg.GetCrntCmdName()

            cmdParams = {} # parameters that will be used in command

            # Set values for optional parameters
            for paramNm in self.myProg.GetOptionalParamNmsForCrntCmd():
                if self.myProg.CrntHasParam(paramNm):
                    cmdParams[paramNm] = self.myProg.GetParamFromCrntCmd(paramNm)
                elif paramNm in list(self.dfltOptnlParamVals.keys()):
                    cmdParams[paramNm] = self.dfltOptnlParamVals[paramNm]
                    if self.verbose:
                        print('    substituting %s into parameter %s'%(self.dfltOptnlParamVals[paramNm],paramNm))
                else:
                    cmdParams[paramNm] = 'NONE'

            # Do overrides for required parameters
            for paramNm in self.myProg.GetParamNmsFromCrntCmd():

                if paramNm in list(self.paramOverrideVals.keys()):
                    cmdParams[paramNm] = self.paramOverrideVals[paramNm]
                    if self.verbose:
                        print('    substituting %s into parameter %s'%(self.paramOverrideVals[paramNm],paramNm))
                else:
                    cmdParams[paramNm] = self.myProg.GetParamFromCrntCmd(paramNm)

            if cmdNm == 'READ':
                self.myCmdRunner.Read(
                    cmdParams['InFileName'],
                    cmdParams['InFieldName'],
                    cmdParams['OutFileName'],
                    cmdParams['NewFieldName'],
                    )

            elif cmdNm == 'READMULTI':
                self.myCmdRunner.ReadMulti(
                    cmdParams['InFileName'],
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    cmdParams['NewFieldNames'],
                    )

            elif cmdNm == 'CVTTOFUZZY':
                self.myCmdRunner.CvtToFuzzy(
                    cmdParams['InFieldName'],
                    cmdParams['TrueThreshold'],
                    cmdParams['FalseThreshold'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'CVTTOFUZZYCURVE':
                self.myCmdRunner.CvtToFuzzyCurve(
                    cmdParams['InFieldName'],
                    cmdParams['RawValues'],
                    cmdParams['FuzzyValues'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'CVTTOFUZZYCAT':
                self.myCmdRunner.CvtToFuzzyCat(
                    cmdParams['InFieldName'],
                    cmdParams['RawValues'],
                    cmdParams['FuzzyValues'],
                    cmdParams['DefaultFuzzyValue'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'MEANTOMID':
                self.myCmdRunner.MeanToMid(
                    cmdParams['InFieldName'],
                    cmdParams['IgnoreZeros'],
                    cmdParams['FuzzyValues'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'COPYFIELD':
                self.myCmdRunner.CopyField(
                    cmdParams['InFieldName'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'NOT':
                self.myCmdRunner.FuzzyNot(
                    cmdParams['InFieldName'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'OR':
                self.myCmdRunner.FuzzyOr(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'AND':
                self.myCmdRunner.FuzzyAnd(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'EMDSAND':
                self.myCmdRunner.FuzzyEMDSAnd(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'ORNEG':
                self.myCmdRunner.FuzzyOrNeg(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'XOR':
                self.myCmdRunner.FuzzyXOr(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'SUM':
                self.myCmdRunner.SumFlds(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'MIN':
                self.myCmdRunner.MinFlds(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'MAX':
                self.myCmdRunner.MaxFlds(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'MEAN':
                self.myCmdRunner.MeanFlds(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'UNION':
                self.myCmdRunner.FuzzyUnion(
                    cmdParams['InFieldNames'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'DIF':
                self.myCmdRunner.DifFlds(
                    cmdParams['StartingFieldName'],
                    cmdParams['ToSubtractFieldName'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'SELECTEDUNION':
                self.myCmdRunner.FuzzySelectedUnion(
                    cmdParams['InFieldNames'],
                    cmdParams['TruestOrFalsest'],
                    cmdParams['NumberToConsider'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'WTDUNION':
                self.myCmdRunner.FuzzyWeightedUnion(
                    cmdParams['InFieldNames'],
                    cmdParams['Weights'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'WTDEMDSAND':
                self.myCmdRunner.FuzzyEMDSWeightedAnd(
                    cmdParams['InFieldNames'],
                    cmdParams['Weights'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'WTDMEAN':
                self.myCmdRunner.WeightedMean(
                    cmdParams['InFieldNames'],
                    cmdParams['Weights'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'WTDSUM':
                self.myCmdRunner.WeightedSum(
                    cmdParams['InFieldNames'],
                    cmdParams['Weights'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'CALLEXTERN':
                self.myCmdRunner.CallExtern(
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'SCORERANGEBENEFIT':
                self.myCmdRunner.ScoreRangeBenefit(
                    cmdParams['InFieldName'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                    )

            elif cmdNm == 'SCORERANGECOST':
                self.myCmdRunner.ScoreRangeCost(
                    cmdParams['InFieldName'],
                    cmdParams['OutFileName'],
                    self.myProg.GetCrntResultName()
                )

            else:
                raise Exception(
                    'ERROR: Unable to interpret command:\n'+
                    '  %s'%self.myProg.GetCrntCmdString()
                    )

            # if cmdNm == 'READ'...elif...else:

            # exit work loop if there is not another command to process
            if not self.myProg.NextCmd():
                break;

        # while True

        if self.verbose: print('  Finish()')
        self.myCmdRunner.Finish() # finish final tasks

    # def RunProgram(self):

    def PrintCmdTree(self):
        print(self.myProg.GetCmdTreeAsString())

    def GetAllResultNames(self):
        return self.myProg.GetAllResultNames()

    def GetCmdTree(self):
        return self.myProg.GetCmdTreeAsString()

    def PrintCRNotice(self):
        EEMSUtils().PrintCRNotice()

    def GetCRNotice(self):
        return EEMSUtils().GetCRNotice()

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        return self
    # def __exit__(self,exc_type,exc_value,traceback):

# class EEMSInterpreter(object):
######################################################################

######################################################################
# EEMSUtils
######################################################################
# Utilities used to make an EEMS life easier
# This class may be used as is, but is called Base, as extension of it
# may prove valuable.
#
# Revision History
#
# 2014.02.17 - tjs
#
# Gathered up and shoved together
#
######################################################################

class EEMSUtils(object):

    EEMSCopyRightNotice =  \
    '######################################################################\n'+ \
    '#\n'+ \
    '# EEMS 2.0\n'+ \
    '#\n'+ \
    '# Copyright 2014\n'+ \
    '# Tim Sheehan, Conservation Biology Institute\n'+ \
    '#\n'+ \
    '# This code is distributed \'as is.\'\n'+ \
    '# \n'+ \
    '# Others may utilize this code directly and in derivative works as\n'+ \
    '# long as it includes this notice.\n'+ \
    '#\n'+ \
    '# Real notice needs to be inserted here.\n'+ \
    '######################################################################\n'

    def __enter__(self):
        return self
    # def __enter__(self):


######################################################################
#  EEMSUtils.OptimizeEEMSReading(EEMSInFNm,EEMSOutFNm):
######################################################################
#
# Read a .eem file, combine all the reads that can be combined
# so that reading is optimized. The resulting .eem file should be
# functionally equivalent to the first, but possibly more efficient.
#
# This method was written to help with the ArcGIS version of EEMS.
#
# Note: EEMS syntax is assumed to be correct by this method.
#
# Revision History
#
# 2014.02.14 - tjs
#
# Gathered up and shoved together
#
######################################################################

    def OptimizeEEMSReading(self,EEMSInFNm,EEMSOutFNm):
        inFile = open(EEMSInFNm,'rU')
        readLines = {}
        noReadLines = []

        for line in inFile:
            line = line.rstrip()

            if not re.match('^\s*READ',line):
                noReadLines.append(line)
                continue

            inFNm = re.search('InFileName\s*=\s*(.*?)[,\)]',line).groups()[0]
            if re.search('OutFileName\s*=\s*(.*?)[,\)]',line):
                outFNm = re.search('OutFileName\s*=\s*(.*?)[,\)]',line).groups()[0]
            else:
                outFNm = 'NONE'

            if re.match('^\s*READMULTI',line):
                inFldNms = re.split('\s*,\s*',re.search('InFieldNames\s*=\s*\[(.*)\][,\)]',line).groups()[0])
            else:
                inFldNms = [re.search('InFieldName\s*=\s*(.*?)[,\)]',line).groups()[0]]

            if inFNm in list(readLines.keys()):
                if outFNm in readLines[inFNm]:
                    readLines[inFNm][outFNm] += inFldNms
                else:
                    readLines[inFNm][outFNm] = inFldNms
            else:
                readLines[inFNm] = {outFNm:inFldNms}

        # for line in inFile:

        inFile.close()

        outFile = open(EEMSOutFNm,'w')

        for inFNm in list(readLines.keys()):
            for outFNm in list(readLines[inFNm].keys()):
                if outFNm == 'NONE':
                    outFile.write('READMULTI(InFileName = %s,InFieldNames = [%s])\n'%
                                  (inFNm,','.join(readLines[inFNm][outFNm]))
                                  )
                else:
                    outFile.write('READMULTI(InFileName = %s,InFieldNames = [%s],OutFileName = %s)\n'%
                                  (inFNm,','.join(readLines[inFNm][outFNm]),outFNm)
                                  )
        # for inFNm in readLines.keys():

        for line in noReadLines:
            outFile.write('%s\n'%line)

        outFile.close

    # def OptimizeEEMSReading(EEMSInFNm,EEMSOutFNm):

    def PrintCRNotice(self):
        print(self.EEMSCopyRightNotice)

    def GetCRNotice(self):
        return self.EEMSCopyRightNotice

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        return self
    # def __exit__(self,exc_type,exc_value,traceback):

# class EEMSUtils(object):
