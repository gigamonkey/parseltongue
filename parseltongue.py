#
# Simple PEG parser framework.
#

import re

verbose = False
depth = 0


class Input:

    def ok(self, next, r): return True, next, r

    def fail(self): return False, self, None

    def match(self, matcher, grammar): raise Exception("abstract")

    def match_eof(self): raise Exception("abstract")

    def match_string(self, s): raise Exception("abstract")

    def match_char_predicate(self, predicate): raise Exception("abstract")

    def match_re(self, regex): raise Exception("abstract")

    def position(self): raise Exception("abstract")


class TextInput(Input):

    def __init__(self, text, position=0):
        self.text = text
        self.pos = position

    def next(self, newpos):
        return TextInput(self.text, newpos)

    def match(self, matcher, grammar):
        global depth
        indent = ' ' * depth
        if verbose:
            print('{}Matching {} at {}'.format(indent, matcher, self.pos))
        depth += 1
        ok, next, r = matcher.match(grammar, self)
        depth -= 1
        if verbose:
            if ok:
                msg = '{}{} matched at {} up to {} returning {}'
                start = self.pos
                end = next.pos
                print(msg.format(indent, matcther, start, end, r))
            else:
                print('{}{} failed at {}'.format(indent, matcher, self.pos))
        return ok, next, r

    def match_eof(self):
        return self.pos >= len(self.text), self, None

    def match_string(self, s):
        p = self.pos
        end = p + len(s)
        if self.text[p:end] == s:
            return self.ok(self.next(end), s)
        else:
            return self.fail()

    def match_char_predicate(self, predicate):
        p = self.pos
        if p < len(self.text) and predicate(self.text[p]):
            return self.ok(self.next(p + 1), self.text[p])
        else:
            return self.fail()

    def match_re(self, regex):
        m = regex.match(self.text, self.pos)
        if m is not None:
            return self.ok(self.next(m.end()), m.group(0))
        else:
            return self.fail()

    def position(self):
        return self.pos


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

    def match(self, grammar, input): pass

    def then(self, expr):
        return SequenceMatcher([self, match(expr)])

    def returning(self, x):
        if callable(x):
            return Builder(self, x)
        elif isinstance(x, int):
            return Builder(self, lambda r: r[x])
        else:
            return Builder(self, lambda _: x)

    def text(self, fn=None):

        def extract(r):
            s = ''.join(x for x in r if x is not None)
            return s if fn is None else fn(s)

        return Builder(self, extract)

    def accept(self, visitor):
        raise Exception('accept not implemented')


class SingleExprMatcher(Matcher):

    def __init__(self, expr):
        self.expr = expr

    def __eq__(self, other):
        return type(self) == type(other) and self.expr == other.expr

    def __hash__(self):
        return hash((type(self), self.expr if type(self.expr) != list else tuple(self.expr)))

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self._expr_str())

    def _expr_str(self):
        return str(self.expr)

class Builder(Matcher):

    def __init__(self, preceeding, fn):
        self.preceeding = preceeding
        self.fn = fn

    def __str__(self):
        return 'Builder({})'.format(self.preceeding)

    def match(self, grammar, input):
        ok, next, r = input.match(self.preceeding, grammar)
        if ok:
            return input.ok(next, self.fn(r))
        else:
            return input.fail()

    def accept(self, visitor):
        new_p = self.preceeding.accept(visitor)
        b = self if new_p == self.preceeding else Builder(new_p, self.fn)
        return visitor.visit_builder(b)


class RuleMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        return input.match(grammar[self.expr], grammar)

    def accept(self, visitor): return visitor.visit_rule_matcher(self)


class StringMatcher(SingleExprMatcher):

    def _expr_str(self):
        escaped = self.expr.replace('\r', '\\r')
        escaped = escaped.replace('\n', '\\n')
        escaped = escaped.replace('\t', '\\t')
        return escaped

    def match(self, grammar, input):
        return input.match_string(self.expr)

    def accept(self, visitor): return visitor.visit_string_matcher(self)


class CharMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        return input.match_char_predicate(self.expr)

    def accept(self, visitor): return visitor.visit_char_matcher(self)


class RegexMatcher(SingleExprMatcher):

    def __init__(self, pattern):
        super().__init__(pattern)
        self.re = re.compile(pattern)

    def match(self, grammar, input):
        return input.match_re(self.re)

    def accept(self, visitor): return visitor.visit_regex_matcher(self)


class SequenceMatcher(SingleExprMatcher):

    def _expr_str(self):
        return ', '.join(str(e) for e in self.expr)

    def then(self, expr):
        return SequenceMatcher(self.expr + [match(expr)])

    def match(self, grammar, input):
        results = []
        new_input = input
        for e in self.expr:
            ok, new_input, r = new_input.match(e, grammar)
            if ok:
                results.append(r)
            else:
                return input.fail()
        return input.ok(new_input, results)

    def accept(self, visitor):
        m = SequenceMatcher([e.accept(visitor) for e in self.expr])
        return visitor.visit_sequence_matcher(m)


class ChoiceMatcher(SingleExprMatcher):

    def _expr_str(self):
        return ', '.join(str(c) for c in self.expr)

    def match(self, grammar, input):
        for c in self.expr:
            ok, next, result = input.match(c, grammar)
            if ok:
                return input.ok(next, result)
        return input.fail()

    def accept(self, visitor):
        m = ChoiceMatcher([c.accept(visitor) for c in self.expr])
        return visitor.visit_choice_matcher(m)


class StarMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        results = []
        while True:
            ok, next, r = input.match(self.expr, grammar)
            assert next.position() > input.position() if ok else True
            if ok:
                results.append(r)
                input = next
                continue
            else:
                break
        return input.ok(input, results)

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else StarMatcher(new_expr)
        return visitor.visit_star_matcher(m)


class PlusMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        results = []
        new_input = input
        while True:
            ok, next, r = new_input.match(self.expr, grammar)
            if ok:
                results.append(r)
                new_input = next
                continue
            else:
                break
        if len(results) > 0:
            return input.ok(new_input, results)
        else:
            return input.fail()

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else PlusMatcher(new_expr)
        return visitor.visit_plus_matcher(m)


class OptionalMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        ok, next, r = input.match(self.expr, grammar)
        if ok:
            return input.ok(next, r)
        else:
            return input.ok(input, None)

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else OptionalMatcher(new_expr)
        return visitor.visit_optional_matcher(m)


class AndMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        ok, _, _ = input.match(self.expr, grammar)
        if ok:
            return input.ok(input, None)
        else:
            return input.fail()

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else AndMatcher(new_expr)
        return visitor.visit_and_matcher(m)


class NotMatcher(SingleExprMatcher):

    def match(self, grammar, input):
        ok, _, _ = input.match(self.expr, grammar)
        if not ok:
            return input.ok(input, None)
        else:
            return input.fail()

    def accept(self, visitor):
        new_expr = self.expr.accept(visitor)
        m = self if new_expr == self.expr else NotMatcher(new_expr)
        return visitor.visit_not_matcher(m)


class EofMatcher(Matcher):

    def __eq__(self, other):
        return type(self) == type(other)

    def __hash__(self):
        return id(self)

    def match(self, grammar, input):
        return input.match_eof()

    def accept(self, visitor): return visitor.visit_eof_matcher(self)


class TokenMatcher(Matcher):

    def __init__(self, matcher, ignore):
        self.matcher = matcher
        self.ignore = ignore
        self.m = star(ignore).then(matcher).then(star(ignore)).returning(1)

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.matcher == other.matcher and
                self.ignore == other.ignore)

    def __hash__(self):
        return hash((type(self), self.matcher, self.ignore))

    def __str__(self):
        m = self.matcher
        i = self.ignore
        return 'TokenMatcher({}, ignoring={})'.format(m, i)

    def match(self, grammar, input):
        return input.match(self.m, grammar)

    def accept(self, visitor):
        new_m = self.matcher.accept(visitor)
        new_i = self.ignore.accept(visitor)
        return visitor.visit_token_matcher(TokenMatcher(new_m, new_i))

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
    return input.match(grammar[init], grammar)

eof = EofMatcher()
