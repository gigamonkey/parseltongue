#!/usr/bin/env python3

from parseltongue import *


def combine(args):
    first, rest = args
    if rest:
        op, expr = rest
        return (op, first, expr)
    else:
        return first


def tok(s):
    return token(literal(s), str.isspace)

def punc(m):
    return m.returning(Nothing)


def binary(left, op, right):
    return match(left).then(optional(tok(op).then(right))).returning(combine)

p = {
    'expression':    binary('term', '+', 'expression'),
    'parenthesized': punc(tok('(')).then('expression').then(punc(tok(')'))),
    'factor':        choice('parenthesized', 'number'),
    'term':          binary('factor', '*', 'term'),
    'number':        star(str.isdigit).text(int)
}

if __name__ == '__main__':

    input = TextInput('1234 + 4567 * 9876 * (23 + 45)')

    ok, _, r = parse(p, 'expression', input)
    print(r if ok else 'Parse failed')
