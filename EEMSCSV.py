#!/opt/local/bin/python

# import the classes needed to create a version of EEMS
import re
import numpy as np
from EEMSBasePackage import EEMSCmdRunnerBase
from EEMSBasePackage import EEMSInterpreter

# Create the EEMSCmdRunner class, by overloading the
# necessary methods from the EEMSCmdRunnerBase class.
# An object of this class will be handed to the interpreter
# and allow EEMS to run.
class EEMSCmdRunner(EEMSCmdRunnerBase):
    def _WriteFldsToFiles(self):
        # Create a map of files and fields
        outFileMap = self._CreateOutFileMap()

        # Go through outFileMap and write the fields to each file
        for outFNm in outFileMap.keys():
            if outFNm != 'NONE':
                outFile = open(outFNm,'w')

                # write field names
                outFile.write(','.join(outFileMap[outFNm])+'\n')
                
                # write values to file
                outChunk = ''
                rowMax = 100000
                rowCnt = 0
                for rowNdx in range(self.arrayShape[0]): # unique to csv!
                    outVals = []
                    for fldNm in outFileMap[outFNm]:
                        outVals.append(self.EEMSFlds[fldNm]['data'][rowNdx])
                    outChunk += ','.join([str(x) for x in outVals])+'\n'
                    rowCnt += 1

                    if rowCnt >= rowMax:
                        outFile.write(outChunk)
                        outChunk = ''
                        rowCnt = 0
                # for rowNdx in range(self.arrayShape[0]): # unique to csv!

                outFile.write(outChunk)

                outFile.close()

    # def _WriteFldsToFile(self):

########################################################################
# Public methods
########################################################################

    def ReadMulti(
        self,
        inFileName,
        inFieldNames,
        outFileName
        ):

        inFile = open(inFileName,'rU')
        line = inFile.readline()
        line = line.rstrip('\r\f\n')
        line = re.sub('"','',line)

        fileFldNms = line.split(',')

        # Confirm all inFieldNames in input file
        for inFldNm in inFieldNames:
            if inFldNm not in fileFldNms:
                raise Exception(
                    '\n********************ERROR********************\n'+
                    'Cannot read field *%s* from file %s.\n'%(inFldNm,inFileName))
            
        # determine inFieldNames col ndxs in input file
        tmpColData = {}
        colNdx = 0
        for fileFldNm in fileFldNms:
            if fileFldNm in inFieldNames:
                tmpColData[fileFldNm] = {'colNdx':colNdx,'data':[]}
            colNdx += 1

        # Load in data from lines
        line = inFile.readline()

        while line != '':
            line = line.rstrip('\r\f\n')
            line = re.sub('"','',line)
            inTokens = line.split(',')

            for fldNm in tmpColData.keys():
                try:
                    fldVal = float(inTokens[tmpColData[fldNm]['colNdx']])
                except ValueError:
                    fldVal = float('nan')

                tmpColData[fldNm]['data'].append(fldVal)

            # for fldNm in tmpColData.keys():

            line = inFile.readline()

        # while line != '':

        # Add fields to EEMSFlds
        for fldNm in tmpColData.keys():
            self._AddFieldToEEMSFlds(outFileName,fldNm,np.array(tmpColData[fldNm]['data']))
                    
        inFile.close()

    # def ReadMulti(...)

    def Finish(self):
        self._WriteFldsToFiles()


# class EEMSCmdRunner(EEMSCmdRunnerBase):                                            
########################################################################

########################################################################
# Executable code starts here
########################################################################

# Start here parsing args, create interpreter, and execute.

myInterp = EEMSInterpreter('/Users/timsheehan/Projects/EEMS/Dev/TimTst.eem',EEMSCmdRunner())
myInterp.PrintCRNotice()
myInterp.PrintCmdTree()
myInterp.RunProgram()


