# Description: Reporting
# Documentation: algorithms.txt

from __future__ import print_function

class Scope(object):
    def __init__(self, name):
        self.name = name
        self.textSet = []
        self.reportIndex = 0

    def insert(self, text, type):
        self.textSet.append((text, type))

class ScopeGuard(object):
    def __init__(self, reporter, name):
        self.name_ = name
        self.reporter_ = reporter
        self.open_ = False

    def __enter__(self):
        self.open()

    def __exit__(self, type, value, traceback):
        self.close()

    def name(self):
        return self.name_

    def isOpen(self):
        return self.open_

    def open(self):
        if not self.open_:
            self.reporter_.openScope(self.name_)
            self.open_ = True

    def close(self):
        if self.open_:
            self.reporter_.closeScope(self.name_)
            self.open_ = False

class Reporter(object):
    def __init__(self):
        # A set of reporting scopes.
        self.scopeSet = []
        self.disabledSet = set()
        self.warnings_ = 0
        self.errors_ = 0
        self.scopeSet.append(Scope('global'))
        self.spaceBeforeNext = False

    def errors(self):
        return self.errors_

    def warnings(self):
        return self.warnings_

    def openScope(self, name):
        scope = Scope(name)
        self.scopeSet.append(scope)
        
        text = [None]
        text += self.heading(name, len(self.scopeSet) - 1)
        text.append(None)
        
        self.report(text, 'heading', True)

    def closeScope(self, name):
        assert len(self.scopeSet) > 0 and name == self.scopeSet[-1].name
        self.scopeSet.pop()

    def enable(self, type, value = True):
        if value:
            if type in self.disabledSet:
                self.disabledSet.remove(type)
        else:
            if not type in self.disabledSet:
                self.disabledSet.add(type)

    def disable(self, type):
        self.enable(type, False)        

    def enabled(self, type):
        return type not in self.disabledSet

    def report(self, text, type, lazy = False):
        if isinstance(text, basestring) or (text is None):
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
            text = [None, '[' + type + ']'] + text + [None];
            self.report(text, type, False)
            if self.enabled(type):
               self.warnings_ += 1

    def reportDebug(self, text, type):
        if isinstance(text, basestring):
            self.reportWarning([text], type)
            return 

        if len(text) > 0:
            text = [None, '[' + type + ']'] + text + [None];
            self.report(text, type, False)

    def reportError(self, text, type):
        if isinstance(text, basestring):
            self.reportError([text], type)
            return 

        if len(text) > 0:
            text = [None, '[' + type + ']!'] + text + [None]
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
                    #print('(' + type + ')')
                    for line in text:
                        if line is None:
                            self.spaceBeforeNext = True
                            continue
                        
                        if self.spaceBeforeNext:
                            print()
                            self.spaceBeforeNext = False

                        print(line.encode("ascii", "backslashreplace"))
            scope.reportIndex = n


