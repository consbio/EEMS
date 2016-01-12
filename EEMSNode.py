########################################################################
# EEMSNode.py

# EEMS: Environmental Evaluation Modeling System

# A modeling system based very closely on EMDS. Allows for implementation
# of logic models based primarily on fuzzy logic.

# Script by Tim Sheehan, with portions based on work done by Brendan Ward

# Tim Sheehan
# Ecological Modeler
# Conservation Biology Institute
# www.consbio.org

# The overall idea behind EEMS in ArcGIS is

# Create an input/results table, feature class, or shapefile 
#   with input values

# Implement the desired logic model using EEMS commands in model
#   builder, fed by the input/results table. This creates a .eem
#   command file.

# Using the EEMS model run tool, use the .eem file and the input/
# results table to run the model and store the results in the
# input/results file.

# This script, EEMSNode.py, is the script used by the EEMS commands
# to generate lines in the .eem file.

# Dev History:

# 2012.02.24 tjs
#   Model Builder command interfaces built,
#   and individually tested.
# 2014.01.22 tjs
#   Recoded the parsing and added CVTTOFUZZYCURVE
# 2014.01.22 tjs
#   Redesigned EEMS command format and implemented this. Added
#   EEMSParseUtils as a module. This file now builds EEMS
#   commands for the new command syntax and uses EEMSParseUtils
#   to do error checking of the EEMS commands.
#
#   Also added more verbose reporting for the commands
#   being executed by this file.
#
# 2014.01.29 tjs
#  EEMSParseUtils further developed into the EEMSCmd class. This class
#  now being used in this script
#   
# 2014.09.12 - tjs
#
# Added commands MEANTOMID,SCORERANGEBENEFIT, SCORERANGECOST. Changed
# EEMSCmd import to the class withing EEMSBasePackage.
#
########################################################################

import arcpy,os,csv,re,time # arc library
from arcpy.sa import *
from arcpy import env

# import EEMSCmd
from EEMSBasePackage import EEMSCmd

########################################################################
# Globals for control, etc
DEBUG = True
MODELBUILDER = True
########################################################################

def OutMsg(lmsg):
    if MODELBUILDER:
        arcpy.AddMessage('%s'%(lmsg))
    else:
        print(lmsg);
# def OutMsg(msg):

def ProfileTime(outStr):
    OutMsg("%7.3f %s"%(time.clock(),outStr))
# def ProfileTime(outStr):

def WriteLineToFile(fNm,line):
    lOutFile = open(fNm,'a')
    lOutFile.write('%s\n'%(line))
    lOutFile.close()
# def WriteLineToFile(fNm,line):

########################################################################
# Processing starts here
########################################################################

# Script is designed to interface with different Arc dialog boxes,
# with different numbers of arguments, depending on the command

####
# Code for new EEMS command structure
###
cmd = arcpy.GetParameterAsText(0)
eemsCmds = []

params = arcpy.GetParameterInfo()

# Log information about the command being run to the
# Arc console
OutMsg('\n-----------------------------------------------------------------')
OutMsg('Executing Arc EEMS Node Command:')
for ndx in range(0,arcpy.GetArgumentCount()):
    OutMsg('  '+params[ndx].displayName+':  '+arcpy.GetParameterAsText(ndx))
OutMsg('-----------------------------------------------------------------\n')

# Build an EEMS command from the input parameters

outNdx = None

if cmd == 'READ':
    inTblNm = arcpy.GetParameterAsText(1)
    inFldNm = arcpy.GetParameterAsText(2)
    cmdFileNm = arcpy.GetParameterAsText(3)
    outFldNm = inFldNm
    outNdx = 4

    eemsCmds.append('%s(InFileName = %s, InFieldName = %s,OutFileName = EEMSArcOutDflt)'%(cmd,inTblNm,inFldNm))

elif cmd == 'CVTTOFUZZY':
    inFldNms = arcpy.GetParameterAsText(1)
    falseThresh = arcpy.GetParameterAsText(2)
    trueThresh = arcpy.GetParameterAsText(3)
    outFldNm = arcpy.GetParameterAsText(4)
    if outFldNm == 'DEFAULT':
        outFldNm = inFldNms + 'Fz'
    cmdFileNm = arcpy.GetParameterAsText(5)
    outNdx = 6

    eemsCmds.append('%s = %s(InFieldName = %s, FalseThreshold = %s,TrueThreshold = %s,OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms,falseThresh,trueThresh))

elif cmd == 'SELECTEDUNION':
    inFldNms = ','.join(arcpy.GetParameterAsText(1).split(';'))
    numToSelect = arcpy.GetParameterAsText(2)
    trueOrFalse = arcpy.GetParameterAsText(3)
    outFldNm = arcpy.GetParameterAsText(4)
    cmdFileNm = arcpy.GetParameterAsText(5)
    outNdx = 6

    eemsCmds.append('%s = %s(InFieldNames = [%s], TruestOrFalsest = %s, NumberToConsider = %s,OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms,trueOrFalse,numToSelect))

elif cmd in ['COPYFIELD','NOT']:
    inFldNms = arcpy.GetParameterAsText(1)
    outFldNm = arcpy.GetParameterAsText(2)
    cmdFileNm = arcpy.GetParameterAsText(3)
    outNdx = 4

    eemsCmds.append('%s = %s(InFieldName = %s,OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms))

elif cmd in ['OR','ORNEG','XOR','SUM','MIN','MAX','MEAN','UNION','AND','EMDSAND']:
    inFldNm = ','.join(arcpy.GetParameterAsText(1).split(';'))
    outFldNm = arcpy.GetParameterAsText(2)
    cmdFileNm = arcpy.GetParameterAsText(3)
    outNdx = 4

    eemsCmds.append('%s = %s(InFieldNames = [%s],OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNm))

elif cmd in ['DIF']:
    inFldNm1 = arcpy.GetParameterAsText(1)
    inFldNm2 = arcpy.GetParameterAsText(2)
    outFldNm = arcpy.GetParameterAsText(3)
    cmdFileNm = arcpy.GetParameterAsText(4)
    outNdx = 5

    eemsCmds.append('%s = %s(StartingFieldName = %s, ToSubtractFieldName = %s,OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNm1,inFldNm2))

elif cmd in ['WTDUNION','WTDAND','WTDMEAN','WTDSUM','WTDEMDSAND']:
    inFldNms = ','.join(arcpy.GetParameterAsText(1).split(';'))
    numericArgs = ','.join(arcpy.GetParameterAsText(2).split(';'))
    outFldNm = arcpy.GetParameterAsText(3)
    cmdFileNm = arcpy.GetParameterAsText(4)
    outNdx = 5

    eemsCmds.append('%s = %s(InFieldNames = [%s], Weights = [%s],OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms,numericArgs))

elif cmd == 'CVTTOFUZZYCURVE':
    inFldNms = arcpy.GetParameterAsText(1)
    numerics = arcpy.GetParameterAsText(2)
    outFldNm = arcpy.GetParameterAsText(3)
    if outFldNm == 'DEFAULT':
        outFldNm = inFldNms + 'Fz'
    cmdFileNm = arcpy.GetParameterAsText(4)
    outNdx = 5
    
    # build lists of pairs
    tmpD = {}

    for pair in numerics.split(':'):
        if pair != '':
            x = float(pair.split(',')[0])
            y = float(pair.split(',')[1])
 
            if x in tmpD:
                errMsg = '\n\n****************************** Error Details ******************************\n'
                errMsg += '  Raw values must be unique in CVTTOFUZZYCURVE:\n'
                errMsg += '    Value %f entered more than once\n'%(x)
                errMsg += '  Your command arguments:\n'
                errMsg += '    Input Field Names: %s\n'%(inFldNms)
                errMsg += '    Raw value, Fuzzy value pairs: %s\n'%(numerics)
                errMsg += '    Result Field Name: %s\n'%(outFldNm)
                errMsg += '***************************************************************************'

                raise Exception(errMsg)
            # if x in tmpD:

            tmpD[float(pair.split(',')[0])] = float(pair.split(',')[1])

        # if pair != '':

    xVals = []
    yVals = []

    for key,val in sorted(tmpD.items()):
        xVals.append(key)
        yVals.append(val)

    eemsCmds.append('%s = %s(InFieldName = %s, RawValues = [%s], FuzzyValues = [%s],OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms,','.join(str(x) for x in xVals),','.join(str(y) for y in yVals)))

elif cmd == 'CVTTOFUZZYCAT':
    inFldNms = arcpy.GetParameterAsText(1)
    numerics = arcpy.GetParameterAsText(2)
    outFldNm = arcpy.GetParameterAsText(3)
    if outFldNm == 'DEFAULT':
        outFldNm = inFldNms + 'Fz'
    cmdFileNm = arcpy.GetParameterAsText(4)
    outNdx = 5
    
    # build lists of pairs
    tmpD = {}

    for pair in numerics.split(':'):
        if pair != '':
            x = float(pair.split(',')[0])
            y = float(pair.split(',')[1])
 
            if x in tmpD:
                errMsg = '\n\n****************************** Error Details ******************************\n'
                errMsg += '  Category values must be unique in %s:\n'%cmd
                errMsg += '    Value %f entered more than once\n'%(x)
                errMsg += '  Your command arguments:\n'
                errMsg += '    Input Field Names: %s\n'%(inFldNms)
                errMsg += '    Raw value, Fuzzy value pairs: %s\n'%(numerics)
                errMsg += '    Result Field Name: %s\n'%(outFldNm)
                errMsg += '***************************************************************************'

                raise Exception(errMsg)
            # if x in tmpD:

            tmpD[float(pair.split(',')[0])] = float(pair.split(',')[1])

        # if pair != '':

    xVals = []
    yVals = []

    for key,val in sorted(tmpD.items()):
        xVals.append(key)
        yVals.append(val)

    eemsCmds.append('%s = %s(InFieldName = %s,RawValues = [%s],FuzzyValues = [%s],OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms,','.join(str(x) for x in xVals),','.join(str(y) for y in yVals)))

elif cmd == 'MEANTOMID':
    inFldNms = arcpy.GetParameterAsText(1)
    ignoreZeros = arcpy.GetParameterAsText(2)
    fuzzyVals = arcpy.GetParameterAsText(3)
    outFldNm = arcpy.GetParameterAsText(4)
    cmdFileNm = arcpy.GetParameterAsText(5)
    outNdx = 6

    if fuzzyVals == 'DEFAULT':
        fuzzyVals = [0,0.25,0.5,0.75,1.0]
    else:

        if len(fuzzyVals.split(',')) != 5:

            errMsg = '\n\n****************************** Error Details ******************************\n'
            errMsg += '  Five fuzzy values must be specified in %s:\n'%(cmd)
            errMsg += '    You specified %d\n'%(len(fuzzyVals))
            errMsg += '  Your command arguments:\n'
            errMsg += '    Input Field Names: %s\n'%(inFldNms)
            errMsg += '    Fuzzy values: %s\n'%(fuzzyValsIn)
            errMsg += '    Result Field Name: %s\n'%(outFldNm)
            errMsg += '***************************************************************************'

        # len(fuzzyVals) != 5:

        fuzzyVals = '[{}]'.format(fuzzyVals)

    eemsCmds.append('%s = %s(InFieldName = %s,IgnoreZeros = %s,FuzzyValues = %s, OutFileName = EEMSArcOutDflt)'%
                    (outFldNm,cmd,inFldNms,ignoreZeros,fuzzyVals))

elif cmd in ['SCORERANGEBENEFIT','SCORERANGECOST']:
    inFldNms = arcpy.GetParameterAsText(1)
    outFldNm = arcpy.GetParameterAsText(2)
    cmdFileNm = arcpy.GetParameterAsText(3)
    outNdx = 4

    eemsCmds.append('%s = %s(InFieldName = %s,OutFileName = EEMSArcOutDflt)'%(outFldNm,cmd,inFldNms))

elif cmd == 'EEMSModelInitialize':
    tblNm = arcpy.GetParameterAsText(1)
    eemsDNm = arcpy.GetParameterAsText(2)
    eemsFNm = arcpy.GetParameterAsText(3)

    if not os.path.exists(eemsDNm):
        errMsg = '\n\n****************************** Error Details ******************************\n'
        errMsg += '  Directory for the EEMS command file does not exist in command%s:\n'%cmd
        errMsg += '    Nonexistant directory: %s\n'%eemsDNm
        errMsg += '  Your command arguments:\n'
        errMsg += '    Data Table: %s\n'%tblNm
        errMsg += '    EEMS Program Directory\n'%eemsDNm
        errMsg += '    EEMS Program Name: %s\n'%eemsFNm
        errMsg += '***************************************************************************'
        
        raise Exception(errMsg)
    # if not os.path.exists(eemsDNm):

    cmdFileNm = eemsDNm + os.sep + eemsFNm
    if os.path.isfile(cmdFileNm):
        os.remove(cmdFileNm)

    arcpy.SetParameter(4,tblNm)
    arcpy.SetParameter(5,cmdFileNm)

    # This insures that when the EEMS program is run, the field used to link computed data back to
    # the original input data is in place.
    # This is in close conjunction with EEMSmodelRun.py
    eemsCmds.append('%s(InFileName = %s, InFieldName = %s, OutFileName = EEMSArcOutDflt)'%('READ',tblNm,'CSVID'))
#    eemsCmds.append('%s = COPYFIELD(InFieldName = %s,OutFileName = EEMSArcOutDflt)'%('CSVID','OBJECTID'))

else:
    raise Exception('Illegal Command: %s'%(cmd))

# set the output variable
if outNdx:
    arcpy.SetParameter(outNdx,outFldNm)

# if cmd == 'READ':...elif...elif...else

# This checks the EEMS command, if it is not a valid
# command, and exception is raised by the EEMSCmd constructor
# code and execution is terminated there. If it is a
# valid command, it is written to file.

for eemsCmd in eemsCmds:
    cmd = EEMSCmd(eemsCmd)
    WriteLineToFile(cmdFileNm,eemsCmd)
    # Log message to Arc Console
    OutMsg("Added Line to %s:\n  %s\n"%(cmdFileNm,eemsCmd))

