# import modules needed

from netCDF4 import *
from scipy.io import netcdf
from collections import OrderedDict
import copy

# import the classes needed to create a version of EEMS
import re
import numpy as np
from EEMSBasePackage import EEMSCmdRunnerBase
#from EEMSBasePackage import EEMSInterpreter

# Create the EEMSCmdRunner class, by overloading the
# necessary methods from the EEMSCmdRunnerBase class.
# An object of this class will be handed to the interpreter
# and allow EEMS to run.
class EEMSCmdRunner(EEMSCmdRunnerBase):

    def __init__(self):
        # We need to overload __init__() to create a 
        # class variable for dimensions

        super(EEMSCmdRunner,self).__init__()
        self.dimensions = None
        self.masterMask = None

    def _WriteFldsToFiles(self):
        # Create a map of files and fields
        outFileMap = self._CreateOutFileMap()

        # Go through outFileMap and write the fields to each file
        for outFNm,outFldNms in outFileMap.items():
            
            if outFNm == 'NONE': continue

            with Dataset(outFNm,'w') as outDS:
                # Write dimensions
                for dimNm,dimDict in self.dimensions.items():
                    self.__DictToDimension(dimDict,outDS,dimNm)
                    
                # Now the fields that go into the file

                for fldNm in outFldNms:

                    fldData = self.EEMSFlds[fldNm]['data']

                    outV = outDS.createVariable(
                        fldNm,
                        fldData.dtype,
                        (self.dimensions.keys()),
                        fill_value = self.GetFillValFromLU(fldData.dtype.char)
                        )
                    outV[:] = np.ma.masked_array(fldData, mask = self.masterMask)

                    setattr(outV,'long_name',fldNm)
                    setattr(outV,'description','EEMS model result')
                # for fldNm,fldData in self.EEMSFlds.items():                

            # with Dataset(outFNm,'w') as outDS:

    # def _WriteFldsToFile(self):

    def GetFillValFromLU(self,dTypeNdx):

        DefaultFillValueLU = {
            'NC_FILL_BYTE':-127,
            'NC_FILL_UBYTE':255,
            'NC_FILL_CHAR':0,
            'NC_FILL_SHORT':-32767,
            'NC_FILL_INT':-2147483647L,
            'NC_FILL_FLOAT':9.9692099683868690e+36,
            'NC_FILL_DOUBLE':9.9692099683868690e+36,
            'b':-127,
            'B':255,
            'c':0,
            's':-32767,
            'f':9.9692099683868690e+36,
            'd':9.9692099683868690e+36,
            'i':-2147483647L,
            'l':-2147483647L,
            'int8':-127,
            'uint8':255,
            'int16':-32767,
            'float32':9.9692099683868690e+36,
            'float64':9.9692099683868690e+36,
            'int32':-2147483647L
            }

        return DefaultFillValueLU[dTypeNdx]

    # def GetFillValFromLU(self,dTypeChar):

########################################################################
# Public methods
########################################################################
    def ReadMulti(
        self,
        inFileName,
        inFieldNames,
        outFileName,
        newFieldNames # substitute names for inFieldNames
        ):

        if newFieldNames is not 'NONE':
            inOutNames = dict(zip(inFieldNames,newFieldNames))
        else:
            inOutNames = dict(zip(inFieldNames,inFieldNames))

        with Dataset(inFileName,'r') as inDS:

            for inFldNm,outFldNm in inOutNames.items():

                if inFldNm not in inDS.variables:
                    raise Exception(
                        '\n********************ERROR********************\n'+
                        'Cannot read field *%s* from file %s.\n'%(inFldNm,inFileName))
            
                inV = inDS.variables[inFldNm]

                # Harvest the dimensions from the input. Will need these for output
                # Assumption is that dimensions of all inputs are the same.
                if self.dimensions is None:
                    maskDims = []
                    self.dimensions = OrderedDict()
                    for dimNm in inV.dimensions:
                        self.dimensions[dimNm] = self.__DimensionToDict(inDS.variables[dimNm])
                        maskDims.append(self.dimensions[dimNm]['len'])
                        
                    self.masterMask = np.zeros(maskDims,dtype=bool)
                # if self.dimesions is None:

                if isinstance(inV[:],np.ma.masked_array):
                    self.masterMask = np.ma.mask_or(self.masterMask,inV[:].mask)
                    tmpMask = inV[:].mask
                else:
                    tmpMask = False

                self._AddFieldToEEMSFlds(
                    outFileName,
                    outFldNm,
                    np.ma.masked_array(inV[:],mask=tmpMask,copy=True)
                    )

                # if isinstance(inV[:],np.ma.masked_array):...else...

            # for inFldNm in inFieldNames:

        # with Dataset(inFileName,'r') as inDS:

    # def ReadMulti(...)

    def Finish(self):
        self._WriteFldsToFiles()

################################################################################

    def __DimensionToDict(self,dimV):
        dimDict = {}
        dimDict = {}
        dimDict['data'] = copy.deepcopy(dimV[:])
        dimDict['len'] = len(dimV[:])
        dimDict['dtypeChar'] = dimV.dtype.char
        dimDict['attributes'] = {}
#        for attNm in dir(dimV):
        for attNm in dimV.ncattrs():
            dimDict['attributes'][attNm] = getattr(dimV,attNm)
        return dimDict
    # def __DimensionToDict(self,dimV):
            
    def __DictToDimension(self,dimDict,outDS,dimNm):
        outDS.createDimension(dimNm,dimDict['len'])
        dimV = outDS.createVariable(
            dimNm,
            dimDict['dtypeChar'],
            (dimNm,)
            )
        for attNm,attVal in dimDict['attributes'].items():
            try:
                setattr(dimV,attNm,attVal)
            except:
                print 'attNm failed to copy: {}'.format(attNm)

        dimV[:] = dimDict['data']

    # def __DictToDimension(self,dimDict,outDS,dimNm):

# class EEMSCmdRunner(EEMSCmdRunnerBase):                                            
########################################################################

# ########################################################################
# # Executable code starts here
# ########################################################################

# # Start here parsing args, create interpreter, and execute.

# myInterp = EEMSInterpreter('/Users/timsheehan/Projects/EEMS/Dev/TimTst.eem',EEMSCmdRunner())
# myInterp.PrintCRNotice()
# myInterp.PrintCmdTree()
# myInterp.RunProgram()


