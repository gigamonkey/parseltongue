#!/usr/bin/env python3

from parseltongue import *
from peg import grammar


def combine(args):
    first, rest = args
    if rest:
        op, expr = rest
        return (op, first, expr)
    else:
        return first

def number(args):
    s = ''.join(x for x in args if x is not None)
    return int(s)


g = grammar('math.g')

g.bind('expression', combine)
g.bind('parenthesized', 1)
g.bind('term', combine)
g.bind('number', number)

if __name__ == '__main__':

    input = TextInput('1234 + 4567 * 9876 * ( 23 + 45 )')

    ok, _, r = parse(g, 'expression', input)
    print(r if ok else 'Parse failed')
