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


class Visitor:

    def visit_builder(self, matcher): return matcher
    def visit_rule_matcher(self, matcher): return matcher
    def visit_string_matcher(self, matcher): return matcher
    def visit_char_matcher(self, matcher): return matcher
    def visit_regex_matcher(self, matcher): return matcher
    def visit_sequence_matcher(self, matcher): return matcher
    def visit_choice_matcher(self, matcher): return matcher
    def visit_star_matcher(self, matcher): return matcher
    def visit_plus_matcher(self, matcher): return matcher
    def visit_optional_matcher(self, matcher): return matcher
    def visit_and_matcher(self, matcher): return matcher
    def visit_not_matcher(self, matcher): return matcher
    def visit_eof_matcher(self, matcher): return matcher
    def visit_token_matcher(self, matcher): return matcher


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

    def accept(self, visitor):
        raise Exception('accept not implemented')



class SingleExprMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __eq__(self, other):
        return type(self) == type(other) and self.expr == other.expr

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.expr)


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

    def accept(self, visitor):
        new_preceeding = self.preceeding.accept(visitor)
        b = self if new_preceeding == self.preceeding else Builder(new_preceeding, self.fn)
        return visitor.visit_builder(b)


class RuleMatcher(SingleExprMatcher):

    def _match(self, grammar, input):
        return grammar[self.expr].match(grammar, input)

    def accept(self, visitor): return visitor.visit_rule_matcher(self)

class StringMatcher(SingleExprMatcher):

    def __str__(self):
        return 'StringMatcher(\'{}\')'.format(self.expr).replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')

    def _match(self, grammar, input):
        return input.match_string(self.expr)

    def accept(self, visitor): return visitor.visit_string_matcher(self)

class CharMatcher(SingleExprMatcher):

    def _match(self, grammar, input):
        return input.match_char_predicate(self.expr)

    def accept(self, visitor): return visitor.visit_char_matcher(self)

class RegexMatcher(Matcher):

    def __init__(self, pattern):
        self.pattern = pattern
        self.re = re.compile(pattern)

    def __str__(self):
        return 'RegexMatcher(/{}/)'.format(self.pattern)

    def _match(self, grammar, input):
        return input.match_re(self.re)

    def accept(self, visitor): return visitor.visit_regex_matcher(self)

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

    def accept(self, visitor):
        m = SequenceMatcher([ e.accept(visitor) for e in self.exprs ])
        return visitor.visit_sequence_matcher(m)

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

    def accept(self, visitor):
        m = ChoiceMatcher([ c.accept(visitor) for c in self.choices ])
        return visitor.visit_choice_matcher(m)

class StarMatcher(SingleExprMatcher):

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

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if x == self.expr else StarMatcher(new_expr)
        return visitor.visit_star_matcher(m)


class PlusMatcher(SingleExprMatcher):

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

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if x == self.expr else PlusMatcher(new_expr)
        return visitor.visit_plus_matcher(m)


class OptionalMatcher(SingleExprMatcher):

    def _match(self, grammar, input):
        ok, next, r = self.expr.match(grammar, input)
        if ok:
            return ok, next, r
        else:
            return True, input, None

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else OptionalMatcher(new_expr)
        return visitor.visit_optional_matcher(m)


class AndMatcher(SingleExprMatcher):

    def _match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return ok, input, None

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else AndMatcher(new_expr)
        return visitor.visit_and_matcher(m)


class NotMatcher(SingleExprMatcher):

    def _match(self, grammar, input):
        ok, _, _ = self.expr.match(grammar, input)
        return not ok, input, None

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else NotMatcher(new_expr)
        return visitor.visit_not_matcher(m)


class EofMatcher(Matcher):

    def _match(self, grammar, input):
        return input.eof(), input, None

    def accept(self, visitor): return visitor.visit_eof_matcher(self)

class TokenMatcher(Matcher):

    def __init__(self, matcher, ignore):
        self.matcher = matcher
        self.ignore = ignore
        self.m = star(ignore).then(matcher).then(star(ignore)).returning(1)

    def __str__(self):
        return 'TokenMatcher({}, ignoring={})'.format(matcher, ignore)

    def _match(self, grammar, input):
        return self.m.match(grammar, input)

    def accept(self, visitor):
        new_matcher = self.matcher.accept(visitor)
        new_ignore = self.ignore.accept(visitor)
        return visitor.visit_token_matcher(TokenMatcher(new_ignore, new_ignore))

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

def token(m, ws):
    return TokenMatcher(match(m), match(ws))

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
