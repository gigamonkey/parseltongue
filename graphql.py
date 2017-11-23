#!/usr/bin/env python3

from parseltongue import *

if __name__ == '__main__':

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

    def make_field(r):
        name, arguments, colon, type = r
        return {
            'name': name,
            'arguments': arguments,
            'type': type
        }

    def argument(r):
        name, colon, type, value = r
        return {
            'name': name,
            'type': type,
            'value': value[1] if value else None
        }

    g = {
        'type'          : literal('type').then(plus('ws')).then('name').then(token('{')).then(star('field')).then(token('}')).returning(make_type),
        'name'          : text(plus(str.isalpha)),
        'field'         : match('name').then(optional('arguments')).then(token(':')).then('field_type').returning(make_field),
        'arguments'     : token('(').then(star('argument')).then(token(')')).returning(1),
        'argument'      : match('name').then(token(':')).then('field_type').then(optional(token('=').then('default_value'))).returning(argument),
        'field_type'    : choice('non_nullable', 'name', 'list').then(star('ws')).returning(0),
        'non_nullable'  : choice('name', 'list').then(token('!')).returning(lambda r: ('non-nullable', r[0])),
        'list'          : token('[').then('field_type').then(token(']')).returning(lambda r: ('list', r[1])),
        'ws'            : match(str.isspace),
        'default_value' : choice('int', 'string'),
        'int'           : text(plus(str.isdigit)).returning(int),
        'string'        : literal('"').then(text(star(not_looking_at(literal('"').then(lambda c: True))))).then(literal('"')).returning(1)
    }


    input = TextInput("""type foo {
bar: Int
baz: [String]
quux(blah: Int = 123): Int!
}""")

    import json

    ok, input, r = parse(g, 'type', input)
    if ok:
        print(json.dumps(r, indent=4))
    else:
        print('Parse failed')
        print("consumed '{}'".format(input.consumed()))
        print("remaining '{}'".format(input.remaining()))
        print(json.dumps(r, indent=4))
