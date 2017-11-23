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

    def binary(left, op, right):
        return match(left).then(optional(token(op).then(right))).returning(combine)

    p = {
        'expression':    binary('term', '+', 'expression'),
        'parenthesized': token('(').then('expression').then(token(')')).returning(lambda r: r[1]),
        'factor':        choice('parenthesized', 'number'),
        'term':          binary('factor', '*', 'term'),
        'number':        text(star(str.isdigit)).returning(int),
    }

    input = TextInput('1234 + 4567 * 9876 * (23 + 45)')

    ok, _, r = parse(p, 'expression', input)
    print(r if ok else 'Parse failed')
