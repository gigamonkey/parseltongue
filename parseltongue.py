#
# Simple PEG parser framework.
#

class TextInput:

    def __init__(self, text, position=0):
        self.text = text
        self.position = position

    def next(self, newpos):
        return TextInput(self.text, newpos)

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

class Matcher:

    def then(self, expr):
        return SequenceMatcher([self, match(expr)])

    def returning(self, x):
        return Builder(self, x if callable(x) else lambda _: x)

class Builder(Matcher):

    def __init__(self, preceeding, fn):
        self.preceeding = preceeding
        self.fn = fn

    def match(self, grammar, input):
        ok, next, r = self.preceeding.match(grammar, input)
        if ok:
            return ok, next, self.fn(r)
        else:
            return False, input, None


class RuleMatcher(Matcher):

    def __init__(self, name):
        self.name = name

    def match(self, grammar, input):
        return grammar[self.name].match(grammar, input)


class StringMatcher(Matcher):

    def __init__(self, s):
        self.s = s

    def match(self, grammar, input):
        return input.match_string(self.s)


class CharMatcher(Matcher):

    def __init__(self, p):
        self.p = p

    def match(self, grammar, input):
        return input.match_char_predicate(self.p)

class SequenceMatcher(Matcher):

    def __init__(self, exprs):
        self.exprs = exprs

    def then(self, expr):
        return SequenceMatcher(self.exprs + [match(expr)])

    def match(self, grammar, input):
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

    def match(self, grammar, input):
        for c in self.choices:
            ok, next, result = c.match(grammar, input)
            if ok:
                return ok, next, result
        return False, input


class StarMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, grammar, input):
        results = []
        while True:
            ok, next, r = self.expr.match(grammar, input)
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

    def match(self, grammar, input):
        results = []
        new_input = input
        while True:
            ok, next, r = self.expr.match(grammar, new_input)
            if ok:
                results.append(r)
                new_input = next
                continue
        if len(results) > 0:
            return True, new_input, results
        else:
            return False, input, None

class OptionalMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, grammar, input):
        ok, next, r = self.expr.match(grammar, input)
        if ok:
            return ok, next, r
        else:
            return True, input, None

class AndMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return ok, input, None

class NotMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return not ok, input, None

class TextMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, grammar, input):
        ok, next, r = self.expr.match(grammar, input)
        if ok:
            return ok, next, ''.join(x for x in r if x is not None)
        else:
            return False, input, None
#
# API
#

def match(expr):
    if type(expr) == str:
        #return StringMatcher(expr)
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
    return OptionalMatcher(expr)

def looking_at(expr):
    return AndMatcher(expr)

def not_looking_at(expr):
    return NotMatcher(expr)

def choice(*exprs):
    return ChoiceMatcher([match(e) for e in exprs])

def text(expr):
    return TextMatcher(expr)

def parse(grammar, init, input):
    return grammar[init].match(grammar, input)
