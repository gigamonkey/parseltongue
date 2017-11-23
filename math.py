#!/usr/bin/env python3

from parseltongue import *

if __name__ == '__main__':

    def combine(args):
        first, rest = args
        if rest:
            op, expr = rest
            return (op, first, expr)
        else:
            return first

    def token(s):
        ws = star(match(str.isspace))
        return ws.then(literal(s)).then(ws).returning(lambda r: r[1])

    p = {
        'expression':    match('term').then(optional(token('+').then('expression'))).returning(combine),
        'parenthesized': token('(').then('expression').then(token(')')),
        'factor':        choice('parenthesized', 'number'),
        'term':          match('factor').then(optional(token('*').then('term'))).returning(combine),
        'digit':         match(str.isdigit),
        'number':        text(star('digit')).returning(int),
    }

    input = TextInput('1234 + 4567 * 9876')

    ok, _, r = parse(p, 'expression', input)
    print(r if ok else 'Parse failed')
