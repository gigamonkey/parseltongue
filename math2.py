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

g = grammar('math.g')

g['expression']    = g['expression'].returning(combine)
g['parenthesized'] = g['parenthesized'].returning(1)
g['term']          = g['term'].returning(combine)
g['number']        = g['number'].text(int)

if __name__ == '__main__':

    input = TextInput('1234+4567*9876*(23+45)')

    ok, _, r = parse(g, 'expression', input)
    print(r if ok else 'Parse failed')
