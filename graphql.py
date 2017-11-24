#!/usr/bin/env python3

from parseltongue import *

def token(s):
    ws = star(str.isspace)
    return ws.then(literal(s)).then(ws).returning(1)

def make_type(r):
    t, ws, name, lbrace, fields, rbrace = r
    return {
        'what': t,
        'name': name,
        'fields': fields
    }

def as_text(r):
    return ''.join(x for x in r if x is not None)

def make_field(r):
    name, arguments, colon, type = r
    return {
        'name': name,
        'arguments': arguments,
        'type': type
    }

def make_argument(r):
    name, colon, type, value = r
    return {
        'name': name,
        'type': type,
        'value': value[1] if value else None
    }


g = {
    'type'          : literal('type').then(plus('ws')).then('name').then(token('{')).then(star('field')).then(token('}')),
    'name'          : plus(str.isalpha),
    'field'         : match('name').then(optional('arguments')).then(token(':')).then('field_type'),
    'arguments'     : token('(').then(star('argument')).then(token(')')),
    'argument'      : match('name').then(token(':')).then('field_type').then(optional(token('=').then('default_value'))),
    'field_type'    : choice('non_nullable', 'name', 'list').then(star('ws')),
    'non_nullable'  : choice('name', 'list').then(token('!')),
    'list'          : token('[').then('field_type').then(token(']')),
    'ws'            : match(str.isspace),
    'default_value' : choice('int', 'string'),
    'int'           : plus(str.isdigit),
    'string'        : literal('"').then(text(star(not_looking_at(literal('"').then(lambda c: True))))).then(literal('"')),
}


b = {
    'type'          : make_type,
    'name'          : as_text,
    'field'         : make_field,
    'arguments'     : 1,
    'argument'      : make_argument,
    'field_type'    : 0,
    'non_nullable'  : lambda r: ('non-nullable', r[0]),
    'list'          : lambda r: ('list', r[1]),
    'int'           : lambda r: int(as_text(r)),
    'string'        : 1,
}

grammar = { k : v.returning(b[k]) if k in b else v for k, v in g.items() }


if __name__ == '__main__':

    input = TextInput("""type foo {
bar: Int
baz: [String]
quux(blah: Int = 123): Int!
}""")

    import json

    ok, input, r = parse(grammar, 'type', input)
    if ok:
        print(json.dumps(r, indent=4))
    else:
        print('Parse failed')
        print("consumed '{}'".format(input.consumed()))
        print("remaining '{}'".format(input.remaining()))
        print(json.dumps(r, indent=4))
