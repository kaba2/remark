# -*- coding: utf-8 -*-

# Description: Equation macro
# Detail: Presents mathematics.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import htmlDiv, htmlInject

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
        numberClassName = scope.getString('Equation.number_class_name', 'Equation-Number')

        text.append("''")
        if len(parameter) == 1:
            text[-1] += parameter[0]
        else:
            text += parameter
        
        text[-1] += "''"
        text += htmlInject(['<span class="' + numberClassName + '">' + str(equationNumber) + '</span>'])

        return htmlDiv(text, className, 'div')

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Equation', Equation_Macro())





