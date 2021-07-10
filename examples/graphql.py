#!/usr/bin/env python3

from parseltongue import TextInput
from parseltongue import parse
from parseltongue import text
from peg import grammar

g = grammar("grammars/graphql.g")


def make_type(r):
    t, ws, name, lbrace, eol, fields, rbrace = r
    return {"what": t, "name": name, "fields": fields}


def make_field(r):
    name, arguments, colon, t, ws, eol = r
    return {"name": name, "arguments": arguments, "type": t}


def make_argument(r):
    name, colon, type, value = r
    return {"name": name, "type": type, "value": value[1] if value else None}


b = {
    "type": make_type,
    "field": make_field,
    "arguments": 1,
    "argument": make_argument,
    "non_nullable": lambda r: {"non-nullable": True, "type": r[0]},
    "list": lambda r: ("list", r[1]),
    "int": lambda r: int(text(r)),
    "string": 1,
}

grammar = {k: v.returning(b[k]) if k in b else v for k, v in g.items()}

if __name__ == "__main__":

    text1 = """type Foo {
bar: Int
baz: [String]
quux(blah: Int = 123): Int!
}"""

    import parseltongue

    parseltongue.verbose = False

    input = TextInput(text1)

    import json

    ok, input, r = parse(grammar, "type", input)
    if ok:
        print(json.dumps(r, indent=4))
    else:
        print("Parse failed")
