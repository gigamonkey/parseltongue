#!/usr/bin/env python3

import types

class TextInput:

    def __init__(self, text, position=0):
        self.text = text
        self.position = position

    def next(self, newpos):
        return TextInput(self.text, newpos)

    def match_string(self, s):
        p = self.position
        if self.text[p:p+len(s)] == s:
            return True, self.next(p + len(s)), s
        else:
            return False, self, p

    def match_char_predicate(self, predicate):
        p = self.position
        if p < len(self.text) and predicate(self.text[p]):
            return True, self.next(p + 1), self.text[p]
        else:
            return False, self, p

class Matcher:

    def __call__(self, input):
        return self.match(input)

    def then(self, expr):
        return SequenceMatcher([self, match(expr)])

    def returning(self, fn):
        return Builder(self, fn)

class Builder(Matcher):

    def __init__(self, preceeding, fn):
        self.preceeding = preceeding
        self.fn = fn

    def match(self, input):
        ok, next, r = self.preceeding.match(input)
        if ok:
            return ok, next, self.fn(r)
        else:
            return False, input, None

class StringMatcher(Matcher):

    def __init__(self, s):
        self.s = s

    def match(self, input):
        return input.match_string(self.s)

class CharMatcher(Matcher):

    def __init__(self, p):
        self.p = p

    def match(self, input):
        return input.match_char_predicate(self.p)

class SequenceMatcher(Matcher):

    def __init__(self, exprs):
        self.exprs = exprs

    def then(self, expr):
        return SequenceMatcher(self.exprs + [match(expr)])

    def match(self, input):
        results = []
        new_input = input
        for e in self.exprs:
            ok, new_input, r = e.match(new_input)
            if ok:
                results.append(r)
            else:
                return False, input, None
        return True, new_input, results

class ChoiceMatcher(Matcher):

    def __init__(self, choices):
        self.choices = choices

    def match(self, input):
        for c in self.choices:
            ok, next, result = c.match(input)
            if ok:
                return ok, next, result
        return False, input


class StarMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, input):
        results = []
        while True:
            ok, next, r = self.expr.match(input)
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

    def match(self, input):
        results = []
        new_input = input
        while True:
            ok, next, r = self.expr.match(new_input)
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

    def match(self, input):
        ok, next, r = expr.match(input)
        if ok:
            return ok, next, r
        else:
            return True, input, None

class AndMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, input):
        ok, _, _ = self.expr.match(input)
        return ok, input, None

class NotMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def match(self, input):
        ok, _, _ = self.expr.match(input)
        return not ok, input, None

#
# API
#

def match(expr):
    if type(expr) == str:
        return StringMatcher(expr)
    elif type(expr) == types.FunctionType:
        return CharMatcher(expr)
    else:
        return expr

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
    return OrMatcher([match(e) for e in exprs])

if __name__ == '__main__':

    digit = match(lambda c: c.isdigit())

    number = star(digit).returning(lambda r: int(''.join(r)))

    addition = number.then('+').then(number)

    input = TextInput('1234+4567')

    ok, input, r = addition(input)
    if ok:
        print(r)
    else:
        print('Parse failed')
