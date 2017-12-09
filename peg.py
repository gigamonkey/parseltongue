#!/usr/bin/env python3

from parseltongue import *

def namechar(c):
    return c.isalnum() or c == '_'

def notspace(c):
    return not c.isspace()

def hex(c):
    return c in '0123456789abcdefABCDEF'

def tok(text):
    return token(literal(text), 'ws')

def make_choice(r):
    return ChoiceMatcher([r[0], *[x[1] for x in r[1]]])

def make_sequence(r):
    return r[0] if len(r) == 1 else SequenceMatcher(r)

def any_char(c):
    return True

g = {
    'grammar'         : star('vars').then(star('production')).then(eof).returning(lambda r: { 'vars': r[0], 'rules': r[1] }),
    'vars'            : star('ignored').then(choice('TOKENS', 'WHITESPACE')).returning(1),
    'TOKENS'          : tok('TOKENS: ').then(plus(not_looking_at('eol').then(choice('literal', 'rule')).then(star('ws')).returning(1))).then('eol').returning(lambda r: ('TOKENS', r[1])),
    'WHITESPACE'      : tok('WHITESPACE: ').then('expression').then('eol').returning(lambda r: ('WHITESPACE', r[1])),
    'production'      : star('ignored').then('name').then(tok(':=')).then('expression').then('eol').then(star('ignored')).returning(lambda r: (r[1], r[3])),
    'name'            : plus(namechar).text(),
    'expression'      : choice('choice', 'sequence'),
    'choice'          : match('sequence').then(plus(tok('|').then('sequence'))).returning(make_choice),
    'sequence'        : star(choice('star', 'plus', 'optional', 'and', 'not', 'base_expression').then(star('ws')).returning(0)).returning(make_sequence),
    'base_expression' : choice('regex', 'unicode', 'rule', 'parenthesized', 'literal', 'token'),
    'parenthesized'   : tok('(').then('expression').then(tok(')')).returning(1),
    'regex'           : literal('/').then(plus(not_looking_at(literal('/')).then(any_char).returning(1)).text(RegexMatcher)).then(literal('/')).returning(1),
    'unicode'         : match(star('ws')).then(literal('u+').then(plus(hex)).returning(lambda r: StringMatcher(chr(int(text(r[1]), 16))))).then(star('ws')).returning(1),
    'rule'            : match('name').returning(RuleMatcher),
    'star'            : match('base_expression').then(tok('*')).returning(lambda r: StarMatcher(r[0])),
    'plus'            : match('base_expression').then(tok('+')).returning(lambda r: PlusMatcher(r[0])),
    'optional'        : match('base_expression').then(tok('?')).returning(lambda r: OptionalMatcher(r[0])),
    'and'             : tok('&').then('base_expression').returning(lambda r: AndMatcher(r[1])),
    'not'             : tok('!').then('base_expression').returning(lambda r: NotMatcher(r[1])),
    'literal'         : literal("'").then(star(not_looking_at(literal("'")).then(lambda _: True).text()).text()).then(literal("'")).returning(lambda r: StringMatcher(r[1])),
    'token'           : literal('`').then(plus(not_looking_at(literal('`')).then(notspace).returning(1))).then(literal('`')).returning(1).text(token),
    'ws'              : choice(literal(' '), literal('\t')),
    'eol'             : star('ws').then(literal('\n')),
    'comment'         : star('ws').then(literal('#')).then(star(not_looking_at('eol').then(any_char))).then('eol'),
    'ignored'         : choice('eol', 'comment'),
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
        ok, input, r = parse(g, 'grammar', input)

        if ok:
            variables = dict(r['vars'])
            rules = dict(r['rules'])

            if 'TOKENS' in variables and 'WHITESPACE' in variables:
                visitor = TokenRewriter(variables['TOKENS'], variables['WHITESPACE'])
                rules = { name : rule.accept(visitor) for name, rule in r['rules'] }
            else:
                rules = dict(r['rules'])
            return Grammar(rules)
        else:
            raise Exception("Can't parse {}".format(file))


if __name__ == '__main__':

    import sys
    import json

    import parseltongue

    parseltongue.verbose = False

    r = grammar(sys.argv[1]) if len(sys.argv) > 1 else g
    for a, b in r.items():
        print('{} => {}'.format(a, b))
