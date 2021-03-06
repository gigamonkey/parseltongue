#!/usr/bin/env python3

"Bootstrap grammar that can parse a text-based grammar language."

from parseltongue import AndMatcher
from parseltongue import ChoiceMatcher
from parseltongue import ImplicitMatcher
from parseltongue import NothingMatcher
from parseltongue import NotMatcher
from parseltongue import OptionalMatcher
from parseltongue import PlusMatcher
from parseltongue import RegexMatcher
from parseltongue import RuleMatcher
from parseltongue import SequenceMatcher
from parseltongue import StarMatcher
from parseltongue import StringMatcher
from parseltongue import TextInput
from parseltongue import TokenMatcher
from parseltongue import Visitor
from parseltongue import choice
from parseltongue import eof
from parseltongue import ignoring
from parseltongue import literal
from parseltongue import match
from parseltongue import not_looking_at
from parseltongue import parse
from parseltongue import plus
from parseltongue import star
from parseltongue import text
from parseltongue import token


def namechar(c):
    return c.isalnum() or c == "_"


def notspace(c):
    return not c.isspace()


def hex(c):
    return c in "0123456789abcdefABCDEF"


def tok(text):
    return token(literal(text), "ws")


def make_choice(r):
    return ChoiceMatcher([r[0], *r[1]])


def make_sequence(r):
    return r[0] if len(r) == 1 else SequenceMatcher(r)


def any_char(c):
    return True


g = {
    "grammar": star("vars").then(star("production")).then(eof).returning(lambda r: {"vars": r[0], "rules": r[1]}),
    "vars": ignoring(star("ignored")).then(choice("TOKENS", "WHITESPACE")),
    "TOKENS": tok("TOKENS: ").then(plus(not_looking_at("eol").then(choice("literal", "rule")).then(ignoring(star("ws"))))).then("eol").returning(lambda r: ("TOKENS", r[1])),
    "WHITESPACE": tok("WHITESPACE: ").then("expression").then("eol").returning(lambda r: ("WHITESPACE", r[1])),
    "production": star("ignored").then("name").then(tok(":=")).then("expression").then("eol").then(star("ignored")).returning(lambda r: (r[1], r[3])),
    "name": plus(namechar).text(),
    "expression": choice("choice", "sequence"),
    "choice": match("sequence").then(plus(ignoring(tok("|")).then("sequence"))).returning(make_choice),
    "sequence": star(choice("star", "plus", "optional", "and", "not", "nothing", "implicit", "base_expression").then(star("ws")).returning(0)).returning(make_sequence),
    "base_expression": choice("regex", "unicode", "rule", "parenthesized", "literal", "token"),
    "parenthesized": ignoring(tok("(")).then("expression").then(ignoring(tok(")"))),
    "regex": ignoring(literal("/")).then(plus(not_looking_at(literal("/")).then(any_char)).text(RegexMatcher)).then(ignoring(literal("/"))),
    "unicode": match(star("ws")).then(literal("u+").then(plus(hex)).returning(lambda r: StringMatcher(chr(int(text(r[1]), 16))))).then(star("ws")).returning(1),
    "rule": match("name").returning(RuleMatcher),
    "star": match("base_expression").then(tok("*")).returning(lambda r: StarMatcher(r[0])),
    "plus": match("base_expression").then(tok("+")).returning(lambda r: PlusMatcher(r[0])),
    "optional": match("base_expression").then(tok("?")).returning(lambda r: OptionalMatcher(r[0])),
    "and": tok("&").then("base_expression").returning(lambda r: AndMatcher(r[1])),
    "not": tok("!").then("base_expression").returning(lambda r: NotMatcher(r[1])),
    "nothing": tok("~").then("base_expression").returning(lambda r: NothingMatcher(r[1])),
    "literal": ignoring(literal("'")).then(star(not_looking_at(literal("'")).then(any_char)).text(StringMatcher)).then(ignoring(literal("'"))),
    "token": ignoring(literal("`")).then(plus(not_looking_at(literal("`")).then(notspace)).text()).then(ignoring(literal("`"))),
    "ws": choice(literal(" "), literal("\t")),
    "eol": star("ws").then(literal("\n")),
    "comment": star("ws").then(literal("#")).then(star(not_looking_at("eol").then(any_char))).then("eol"),
    "ignored": choice("eol", "comment"),
    "implicit": ignoring(literal("implicit(")).then(star(not_looking_at(literal(")")).then(any_char))).then(ignoring(literal(")"))).text(ImplicitMatcher),
}


class TokenRewriter(Visitor):
    def __init__(self, tokens, whitespace):
        self.tokens = set(tokens)
        self.whitespace = whitespace

    def visit_string_matcher(self, m):
        return TokenMatcher(m, self.whitespace) if m in self.tokens else m

    def visit_rule_matcher(self, m):
        return TokenMatcher(m, self.whitespace) if m in self.tokens else m


class Grammar:
    def __init__(self, rules):
        self.rules = rules

    def __getitem__(self, key):
        return self.rules[key]

    def bind(self, name, fn):
        self.rules[name] = self.rules[name].returning(fn)

    def bindings(self, bindings):
        for rule, fn in bindings.items():
            self.rules[rule] = self.rules[rule].returning(fn)
        return self

    def parse(self, expression, input):
        import parseltongue

        parseltongue.parse(self.rules, expression, input)


def grammar(file):
    with open(file) as f:
        input = TextInput(f.read())
        ok, input, r = parse(g, "grammar", input)

        if ok:
            variables = dict(r["vars"])
            rules = dict(r["rules"])

            if "TOKENS" in variables and "WHITESPACE" in variables:
                visitor = TokenRewriter(variables["TOKENS"], variables["WHITESPACE"])
                rules = {name: rule.accept(visitor) for name, rule in r["rules"]}
            else:
                rules = dict(r["rules"])
            return Grammar(rules)
        else:
            raise Exception("Can't parse {}".format(file))


if __name__ == "__main__":

    import sys

    import parseltongue

    parseltongue.verbose = False

    r = grammar(sys.argv[1]) if len(sys.argv) > 1 else g
    for a, b in r.rules.items():
        print("{} => {}".format(a, b))
