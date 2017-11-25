#
# Simple PEG parser framework.
#

import re

verbose = False
depth = 0

class TextInput:

    def __init__(self, text, position=0):
        self.text = text
        self.position = position

    def next(self, newpos):
        return TextInput(self.text, newpos)

    def eof(self):
        return self.position >= len(self.text)

    def between(self, next):
        return self.text[self.position:next.position]

    def match_string(self, s):
        p = self.position
        end = p + len(s)
        if self.text[p:end] == s:
            return True, self.next(end), s
        else:
            return False, self, p

    def match_char_predicate(self, predicate):
        p = self.position
        if p < len(self.text) and predicate(self.text[p]):
            return True, self.next(p + 1), self.text[p]
        else:
            return False, self, p

    def match_re(self, regex):
        m = regex.match(self.text, self.position)
        if m is not None:
            return True, self.next(m.end()), m.group(0)
        else:
            return False, self, self.position

    def consumed(self):
        return self.text[:self.position]

    def remaining(self):
        return self.text[self.position:]

class Matcher:

    def then(self, expr):
        return SequenceMatcher([self, match(expr)])

    def match(self, grammar, input):
        global depth
        indent = ' ' * depth
        if verbose: print('{}Matching {} at {}'.format(indent, self, input.position))
        depth += 1
        ok, next, r = self._match(grammar, input)
        depth -= 1
        if verbose:
            if ok:
                print('{}{} matched at {} up to {} returning {}'.format(indent, self, input.position, next.position, r))
            else:
                print('{}{} failed at {}'.format(indent, self, input.position))
        return ok, next, r

    def returning(self, x):
        if callable(x):
            fn = x
        elif isinstance(x, int):
            fn = lambda r: r[x]
        else:
            fn = lambda _: x

        return Builder(self, fn)

    def text(self, fn=None):

        def extract(r):
            return ''.join(x for x in r if x is not None)

        return Builder(self, extract if fn is None else lambda r: fn(extract(r)))



class Builder(Matcher):

    def __init__(self, preceeding, fn):
        self.preceeding = preceeding
        self.fn = fn

    def __str__(self):
        return 'Builder({})'.format(self.preceeding)

    def _match(self, grammar, input):
        ok, next, r = self.preceeding.match(grammar, input)
        if ok:
            return ok, next, self.fn(r)
        else:
            return False, input, None


class RuleMatcher(Matcher):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'RuleMatcher({})'.format(self.name)

    def _match(self, grammar, input):
        ok, next, r = grammar[self.name].match(grammar, input)
        return ok, next, r


class StringMatcher(Matcher):

    def __init__(self, s):
        self.s = s

    def __str__(self):
        return 'StringMatcher(\'{}\')'.format(self.s).replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')

    def _match(self, grammar, input):
        return input.match_string(self.s)


class CharMatcher(Matcher):

    def __init__(self, p):
        self.p = p

    def _match(self, grammar, input):
        return input.match_char_predicate(self.p)


class RegexMatcher(Matcher):

    def __init__(self, pattern):
        self.pattern = pattern
        self.re = re.compile(pattern)

    def __str__(self):
        return 'RegexMatcher(/{}/)'.format(self.pattern)

    def _match(self, grammar, input):
        return input.match_re(self.re)


class SequenceMatcher(Matcher):

    def __init__(self, exprs):
        self.exprs = exprs

    def __str__(self):
        return 'SequenceMatcher({})'.format(', '.join(str(e) for e in self.exprs))

    def then(self, expr):
        return SequenceMatcher(self.exprs + [match(expr)])

    def _match(self, grammar, input):
        results = []
        new_input = input
        for e in self.exprs:
            ok, new_input, r = e.match(grammar, new_input)
            if ok:
                results.append(r)
            else:
                return False, input, None
        return True, new_input, results

class ChoiceMatcher(Matcher):

    def __init__(self, choices):
        self.choices = choices

    def __str__(self):
        return 'ChoiceMatcher({})'.format(', '.join(str(c) for c in self.choices))

    def _match(self, grammar, input):
        for c in self.choices:
            ok, next, result = c.match(grammar, input)
            if ok:
                return ok, next, result
        return False, input, None


class StarMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return 'StarMatcher({})'.format(self.expr)

    def _match(self, grammar, input):
        results = []
        while True:
            ok, next, r = self.expr.match(grammar, input)
            assert next.position > input.position if ok else True
            if ok:
                results.append(r)
                input = next
                continue
            else:
                break
        return True, input, results


class PlusMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return 'PlusMatcher({})'.format(self.expr)

    def _match(self, grammar, input):
        results = []
        new_input = input
        while True:
            ok, next, r = self.expr.match(grammar, new_input)
            if ok:
                results.append(r)
                new_input = next
                continue
            else:
                break
        if len(results) > 0:
            return True, new_input, results
        else:
            return False, input, None

class OptionalMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return 'OptionalMatcher({})'.format(self.expr)

    def _match(self, grammar, input):
        ok, next, r = self.expr.match(grammar, input)
        if ok:
            return ok, next, r
        else:
            return True, input, None

class AndMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return 'AndMatcher({})'.format(self.expr)

    def _match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return ok, input, None

class NotMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return 'NotMatcher({})'.format(self.expr)

    def _match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return not ok, input, None


class EofMatcher(Matcher):

    def _match(self, grammar, input):
        return input.eof(), input, None


#
# API
#

def match(expr):
    if type(expr) == str:
        return RuleMatcher(expr)
    elif callable(expr):
        return CharMatcher(expr)
    else:
        return expr

def literal(expr):
    return StringMatcher(expr)

def star(expr):
    return StarMatcher(match(expr))

def plus(expr):
    return PlusMatcher(match(expr))

def optional(expr):
    return OptionalMatcher(match(expr))

def looking_at(expr):
    return AndMatcher(match(expr))

def not_looking_at(expr):
    return NotMatcher(match(expr))

def choice(*exprs):
    return ChoiceMatcher([match(e) for e in exprs])

def regex(pattern):
    return RegexMatcher(pattern)

def text(r):
    return ''.join(x for x in r if x is not None)

def parse(grammar, init, input):
    return grammar[init].match(grammar, input)

eof = EofMatcher()
