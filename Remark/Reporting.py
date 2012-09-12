# Description: Reporting
# Documentation: algorithms.txt

class Scope(object):
    def __init__(self, name):
        self.name = name
        self.textSet = []
        self.reportIndex = 0

    def insert(self, text, type):
        self.textSet.append((text, type))
        
class Reporter(object):
    def __init__(self):
        # A set of reporting scopes.
        self.scopeSet = []
        self.disabledSet = set()
        self.warnings_ = 0
        self.errors_ = 0
        self.scopeSet.append(Scope('global'))

    def errors(self):
        return self.errors_

    def warnings(self):
        return self.warnings_

    def openScope(self, name):
        scope = Scope(name)
        self.scopeSet.append(scope)
        
        text = ['']
        text += self.heading(name, len(self.scopeSet) - 1)
        #text.append('')
        self.report(text, 'heading', True)

    def closeScope(self, name):
        assert len(self.scopeSet) > 0 and name == self.scopeSet[-1].name
        self.scopeSet.pop()

    def enable(self, type):
        if type in self.disabledSet:
            self.disabledSet.remove(type)

    def disable(self, type):
        self.disabledSet.add(type)

    def enabled(self, type):
        return not self.disabled(type)

    def disabled(self, type):
        return type in self.disabledSet

    def report(self, text, type, lazy = False):
        if isinstance(text, basestring):
            self.report([text], type, lazy)
            return 

        if self.enabled(type):
            self.scope().insert(text, type)
            if not lazy:
                self.updatePrint()

    def reportWarning(self, text, type):
        if isinstance(text, basestring):
            self.reportWarning([text], type)
            return 

        if len(text) > 0:
            text = [''] + ['[' + type + ']'] + text;
            self.report(text, type, False)
            if self.enabled(type):
               self.warnings_ += 1

    def reportError(self, text, type):
        if isinstance(text, basestring):
            self.reportError([text], type)
            return 

        if len(text) > 0:
            text = ['', '[' + type + ']!'] + text
            self.report(text, type, False)
            self.errors_ += 1

    def reportAmbiguousDocument(self, path):
        self.reportWarning('Document ' + path + ' is ambiguous. Picking arbitrarily.',
                           'ambiguous-document')

    def reportMissingDocument(self, path):
        self.reportWarning('Document ' + path + ' not found. Ignoring it.',
                           'missing-document')

    # Private

    def heading(self, name, level):
        text = []
        if level == 1:
            text.append(name)
            text.append('=' * max(len(name), 3))
        elif level == 2:
            text.append(name)
            text.append('-' * max(len(name), 3))
        else:
            text.append('#' * level + ' ' + name)
        return text

    def scope(self):
        return self.scopeSet[-1]

    def updatePrint(self):
        for scope in self.scopeSet:
            n = len(scope.textSet)
            for i in range(scope.reportIndex, n):
                (text, type) = scope.textSet[i]
                if self.enabled(type):
                    #print '(' + type + ')'
                    for line in text:
                        print line
            scope.reportIndex = n


