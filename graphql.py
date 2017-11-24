#!/usr/bin/env python3

from parseltongue import *
from peg import grammar

g = grammar('graphql.g')
g['ws']    = match(lambda c: c in ' \t')
g['alpha'] = match(str.isalnum)
g['digit'] = match(str.isdigit)
g['eol']   = literal('\n')

def token(s):
    ws = star(str.isspace)
    return ws.then(literal(s)).then(ws).returning(1)

def make_type(r):
    t, ws, name, lbrace, eol, fields, rbrace = r
    return {
        'what': t,
        'name': name,
        'fields': fields
    }

def as_text(r):
    return ''.join(x for x in r if x is not None)

def make_field(r):
    name, arguments, colon, t, ws, eol = r
    return {
        'name': name,
        'arguments': arguments,
        'type': t
    }

def make_argument(r):
    name, colon, type, value = r
    return {
        'name': name,
        'type': type,
        'value': value[1] if value else None
    }

b = {
    'type'          : make_type,
    'name'          : as_text,
    'field'         : make_field,
    'arguments'     : 1,
    'argument'      : make_argument,
    'non_nullable'  : lambda r: { 'non-nullable': True, 'type': r[0] },
    'list'          : lambda r: ('list', r[1]),
    'int'           : lambda r: int(as_text(r)),
    'string'        : 1,
}

grammar = { k : v.returning(b[k]) if k in b else v for k, v in g.items() }

if __name__ == '__main__':

    text = """type foo {
bar: Int
baz: [String]
quux(blah: Int = 123): Int!
}"""

    text2 = """type foo {
bar: Int
baz: [String]
quux(blah: Int = 123): Int!
}"""

    import parseltongue

    parseltongue.verbose = False

    input = TextInput(text)

    import json

    ok, input, r = parse(grammar, 'type', input)
    if ok:
        print(json.dumps(r, indent=4))
    else:
        print('Parse failed')
        print("consumed '{}'".format(input.consumed()))
        print("remaining '{}'".format(input.remaining()))
        print(json.dumps(r, indent=4))
