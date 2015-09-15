#! /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# import modules needed

from EEMSNetCDF import EEMSCmdRunner
from EEMSBasePackage import EEMSInterpreter
from sys import argv

# ########################################################################
# # Executable code starts here
# ########################################################################

# # Start here parsing args, create interpreter, and execute.

myInterp = EEMSInterpreter(argv[1],EEMSCmdRunner())
# myInterp.PrintCRNotice()
# myInterp.PrintCmdTree()
myInterp.RunProgram()


