# -*- coding: utf-8 -*-

# Description: Equation macro
# Detail: Presents mathematics.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class Equation_Macro(object):
    def __init__(self, leftSymbol, rightSymbol):
        self.leftSymbol = leftSymbol
        self.rightSymbol = rightSymbol

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

        if len(parameter) >  0:
            parameter[0] = self.leftSymbol + parameter[0]
            parameter[-1] += self.rightSymbol

        text = markdownRegion(parameter, {'class' : bodyClassName, 'remark-content' : 'remark-no-p'})
        text += markdownRegion(
            [str(equationNumber)], 
            {
                'class' : numberClassName,
                'remark-content' : 'text'
            }, 
            'span')

        return markdownRegion(text, {'class' : className})

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Equation', Equation_Macro("''", "''"))
registerMacro('EquationLatex', Equation_Macro('$', '$'))





