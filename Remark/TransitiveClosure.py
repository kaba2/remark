from copy import copy

class Progress(object):
    def __init__(self, depth, value):
        # Integer
        self.depth = depth
        # Codomain
        self.value = value
        assert self.value != None
        # Boolean
        self.reflexive = False

class TransitiveClosure(object):
    def __init__(self, identity, forEachDomain, forEachRelated, function,
                 codomainOperator, report, reflexiveClosure):
        self.identity = identity
        self.forEachDomain = forEachDomain
        self.forEachRelated = forEachRelated
        self.function = function
        self.codomainOperator = codomainOperator
        self.report = report
        self.reflexiveClosure = reflexiveClosure

        # Domain --> Progress
        self.progressSet = {}
        # Set of domain element.
        self.workSet = []

    def work(self):
        def visitIt(x):
            if not x in self.progressSet:
                # This node has not been visited
                # yet. Visit it now.
                self.traverse(x)

        self.forEachDomain(visitIt)

        # Report the closure function, but only
        # for those nodes which are in the domain.
        def reportIt(x):
            progress = self.progressSet.get(x)
            assert progress != None

            self.report(x, progress.value)

        self.forEachDomain(reportIt)

    def traverse(self, x):
        ClosureValueReady = -1
        depth = len(self.workSet)

        # The traverse() function should only
        # be called once for each 'x', so that
        # there should not be an existing entry for
        # the 'x'.
        assert not x in self.progressSet

        # Give the node the identity value of the monoid. 
        # If this node does not refer to any nodes (not 
        # even itself), then it will end up having the identity 
        # value.
        self.progressSet[x] = Progress(depth, copy(self.identity))

        xProgress = self.progressSet[x]

        # Push the node to the list of to-be-handled nodes.
        # Essentially, this list stores the elements of the
        # strongly connected components, with each component
        # being an interval in this list. However, there are
        # also singular nodes in this list which are not
        # strongly connected components (the node must be
        # related to itself to be a strongly connected 
        # component).
        self.workSet.append(x)

        def dealWithIt(y):
            if x == y:
                # The node x is related to itself.
                # Add the function-value to the
                # closure-value.
                xProgress.value = self.codomainOperator(
                    copy(xProgress.value), copy(self.function(x)))
                xProgress.reflexive = True
                return

            # If 'y' has not beed traversed yet...
            if not y in self.progressSet:
                # ... traverse it now.
                self.traverse(y)

            yProgress = self.progressSet[y]
            if yProgress.depth >= 0:
                # After finishing visiting the related nodes,
                # the depth of node x is the minimum of the depths 
                # encountered in children.
                if yProgress.depth < xProgress.depth:
                    xProgress.depth = yProgress.depth
            else:
                # If the node y has a negative depth value, then
                # this means that its closure-value has already
                # been computed.

                assert x != y

                prevValue = copy(xProgress.value)
                assert prevValue != None

                # Add the closure-value of node y to the 
                # closure-value of node x.
                xProgress.value = self.codomainOperator(
                    prevValue, 
                    copy(yProgress.value))

                if xProgress.value == None:
                    print 'Previous:', prevValue,
                    print yProgress.value

                assert xProgress.value != None

                if not yProgress.reflexive:
                    # If the function-value of node y is not
                    # part of the closure-value of node y, then 
                    # add it now to the closure-value of node x.
                    xProgress.value = self.codomainOperator(
                        copy(xProgress.value), 
                        copy(self.function(y)))

        self.forEachRelated(x, dealWithIt)

        # Force a reflexive relation if necessary.
        if self.reflexiveClosure and (not xProgress.reflexive):
            dealWithIt(x)

        if xProgress.depth == depth:
            # If the minimum encountered depth-value is the
            # same as the depth-value of node x, then all the
            # nodes after 'x' in the 'workSet' belong to the 
            # same strongly connected component as node x.

            moreThanOneElement = (self.workSet[-1] != x)
                
            if moreThanOneElement:
                # We have a strongly connected component
                # with at least two elements. These elements
                # all have the same closure-value, which is
                # the combination of the functions-values of
                # the elements. Compute this shared closure-value
                # incrementally.

                index = 0
                while True:
                    index -= 1
                    y = self.workSet[index]
                    assert y in self.progressSet
                    yProgress = self.progressSet[y]

                    if not yProgress.reflexive:
                        # If a node in the component is not reflexive,
                        # then make it so.
                        yProgress.value = self.codomainOperator(
                            copy(yProgress.value), copy(self.function(y)))
                        yProgress.reflexive = True

                    if x != y:
                        # Add the closure-value of node y to the 
                        # closure-value of node x.
                        xProgress.value = self.codomainOperator(
                            copy(xProgress.value), copy(yProgress.value))
                    
                    if self.workSet[index] == x:
                        break

                # Note that the closure-values are not correct yet.
                # They need to copied from node x to the other nodes.
                # This is done next.

            ready = False
            while not ready:
                y = self.workSet[-1]
                assert y in self.progressSet
                yProgress = self.progressSet[y]

                # Mark the node as having a fully-computed
                # closure-value.
                yProgress.depth = ClosureValueReady

                if y == x:
                    # No need to copy the closure-value of 
                    # node x to itself.
                    ready = True
                else:
                    # Copy the closure-value inside the
                    # strongly connected component.
                    yProgress.value = xProgress.value

                # Remove the node from the work-set.
                self.workSet.pop()

def transitiveClosure(identity, forEachDomain, forEachRelated, function,
                      codomainOperator, report, reflexiveClosure):
    algorithm = TransitiveClosure(identity, forEachDomain, forEachRelated,
                      function, codomainOperator, report, reflexiveClosure)
    algorithm.work()

def testTransitiveClosure():
    identity = set()
    relation = {1 : [1, 2], 2 : [2, 4], 3 : [3, 2], 4 : [4, 5], 5 : [5, 4], 6 : [6]}
    function = (lambda x : set([x]))
    closureFunction = {}
    
    def forEachDomain(visit):
        for i in range(1, 8):
            visit(i)

    def forEachRelated(x, visit):
        if not x in relation:
            return
        for y in relation[x]:
            visit(y)

    def codomainOperator(left, right):
        left.update(right)
        return left

    def report(x, f):
        closureFunction[x] = f

    transitiveClosure(identity, forEachDomain, forEachRelated, function,
                      codomainOperator, report, reflexiveClosure = False)
    
    print closureFunction

