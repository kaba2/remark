# -*- coding: utf-8 -*-

# Description: Equation macro
# Detail: Presents mathematics.

from Remark.Macro_Registry import registerMacro

class Equation_Macro(object):
    def name(self):
        return 'Equation'

    def expand(self, parameter, remark):
        text = []

        document = remark.document

        # Tags
        equationNumber = document.tagInteger('Equation.number', None)
        if equationNumber == None:
            document.setTag('Equation.number', ['1'])
            equationNumber = 1
        document.setTag('Equation.number', [repr(equationNumber + 1)])

        # Variables
        scope = remark.scopeStack.top()
        className = scope.getString('Equation.class_name', 'Equation')
        bodyClassName = scope.getString('Equation.body_class_name', 'Equation-Body')
        numberClassName = scope.getString('Equation.number_class_name', 'Equation-Number')

        text.append('<div class = "' + className + '">')
        text.append('<span class = "' + bodyClassName + '">' + "''")
        if len(parameter) == 1:
            text[-1] += parameter[0]
        else:
            text += parameter
        text[-1] += "''" + '</span>'
        text.append('<span class = "' + numberClassName + '">' + 
                    str(equationNumber) + 
                    '</span>')
        text.append('</div>')

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Equation', Equation_Macro())





