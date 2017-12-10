#!/usr/bin/env python3

from parseltongue import *
from peg import grammar

class Variable:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'Variable({})'.format(self.name)

class NamedType:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'NamedType({})'.format(self.name)

class ListType:

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return 'ListType({})'.format(self.type)

class NonNullType:

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return 'NonNullType({})'.format(self.type)




def identity(x): return x

def text(args):
    return ''.join(x for x in args if x is not None)

def value(x):
    return lambda args: x

def to_dict(*fields):
    return lambda args: { k:v for k,v in zip(fields, args) if k is not None}

def operation(selection_set, type='query', name=None, vars=None, directives=None):
    return {
        'type': type,
        'name': name,
        'vars': vars,
        'directives': directives,
        'selection_set': selection_set
    }



def named_operation(args):
    # OperationType Name? VariableDefinitions? Directives? SelectionSet
    selection_set = args[4]
    extra = { k:v for k,v in zip(['type', 'name', 'vars', 'directives'], args[:4])}
    return operation(selection_set, **extra)

def anonymous_query(args):
    return operation(args)

def non_zero(args):
    negsign, d1, ds = args
    n = int('{}{}'.format(d1, ''.join(ds)))
    return n if negsign is None else -n

def make_float(i, f, e):
    return float('{}.{}e{}'.format(i, f, text(e)))

x = {
    'LineTerminator': value('\n'),
    'NamedOperation': named_operation,
    'AnonymousQuery': anonymous_query,
    'Field': to_dict('alias', 'name', 'arguments', 'directives', 'selection_set'),
    'Argument': to_dict('name', 'value'),
    'FragmentSpread': to_dict('name', 'directives'),
    'FragmentDefinition': to_dict('name', 'type', 'directives', 'selection_set'),
    'InlineFragment': to_dict('type', 'directives', 'selection_set'),


    'IntegerPart': identity,
    'Zero': value(0),
    'NonZero': non_zero,

    'FloatJustFrac': lambda args: make_float(args[0], args[1], '0'),
    'FloatJustExp': lambda args: make_float(args[0], '0', args[1]),
    'FloatBoth': lambda args: make_float(*args),
    'FractionalPart': text,
    'ExponentPart': lambda args: '{}{}'.format(args[0] or '+', text(args[1])),

    'BooleanValue': lambda x: x == 'true',

    'StringValue': text,
    'EscapedUnicode': lambda x: chr(int(text(x), 16)),
    'NullValue': value(None),

    'EnumValue': identity,

    'ObjectValue': identity,

    #  Name ':' Value
    'ObjectField': identity,

    'Variable': Variable,

    #  Variable ':' Type DefaultValue?
    'VariableDefinition': identity,

    'NamedType': NamedType,
    'ListType': ListType,
    'NonNullType': NonNullType,

    #  '@' Name Arguments?
    'Directive': to_dict('name', 'arguments')

}


g = grammar('query.g').bindings(x)


if __name__ == '__main__':

    import parseltongue
    import sys

    parseltongue.verbose = False

    verbose = False

    allOkay = True

    def check(rule, text):
        parseltongue.verbose = False
        ok, _, r = parse(g, rule, TextInput(text))
        if ok:
            if verbose:
                print('ok: {} parsed {} => {}'.format(rule, repr(text), r))
        else:
            print('FAIL: {} did not parse {}'.format(rule, repr(text)))
            allOkay = False
            parseltongue.verbose = True
            parse(g, rule, TextInput(text))

    def doc(text):
        check('Document', text)


    # Specific rules
    check('Name', 'name')
    check('Field', 'hero { name }')
    check('Field', 'name')
    check('SelectionSet', '{name}')
    check('WhiteSpace', ' ')
    check('SelectionSet', '{ name }')
    check('OperationType', 'query')
    check('Name', 'HeroNameQuery')
    check('SelectionSet', '{ hero { name } }')
    check('SelectionSet', '{\nhero { name } }')
    check('StringValue', '"1000"')
    check('Value', '"1000"')
    check('Arguments', '(id: "1000")')
    check('Field', 'human(id: "1000")')
    check('VariableDefinition', '$someId: String!')
    check('VariableDefinitions', '($someId: String)')
    check('NonNullType', 'String!')
    check('VariableDefinitions', '($someId: String!)')

    # From https://github.com/graphql/graphql-js/blob/master/src/__tests__/starWarsQuery-test.js
    doc('query HeroNameQuery { hero { name } }')
    doc('query HeroNameQuery { hero { name,title } }')
    doc('query { hero { name } }')
    doc('{ hero { name } }')
    doc('query HeroNameAndFriendsQuery {hero {id name friends {name}}}')
    doc('query HeroNameAndFriendsQuery {\n          hero {\n            id\n            name\n            friends {\n              name\n            }\n          }\n        }\n')
    doc('query NestedQuery {\n          hero {\n            name\n            friends {\n              name\n              appearsIn\n              friends {\n                name\n              }\n            }\n          }\n        }')
    doc('query FetchLukeQuery {human(id: "1000") {name}}')
    doc('query FetchSomeIDQuery($someId: String!) { human(id: $someId) {name} }')
    doc('query FetchLukeAliased {luke: human(id: "1000") {name}}')
    doc('query FetchLukeAndLeiaAliased {luke: human(id: "1000") {name} leia: human(id: "1003") {name}}')
    doc('query DuplicateFields {luke: human(id: "1000") {name homePlanet} leia: human(id: "1003") {name homePlanet}}')
    doc('query UseFragment {luke: human(id: "1000") {...HumanFragment} leia: human(id: "1003") {...HumanFragment}} fragment HumanFragment on Human {name homePlanet}')
    doc('query CheckTypeOfR2 {hero {__typename name}}')
    doc('query CheckTypeOfLuke {hero(episode: EMPIRE) {__typename name}}')
    doc('query HeroNameQuery {hero {name secretBackstory}}')
    doc('query HeroNameQuery {hero {name friends {name secretBackstory}}}')
    doc('query HeroNameQuery {mainHero: hero {name story: secretBackstory}}')


    # From https://github.com/graphql/graphql-js/blob/master/src/__tests__/starWarsValidation-test.js
    doc('query NestedQueryWithFragment {hero {...NameAndAppearances friends {...NameAndAppearances friends {...NameAndAppearances}}}} fragment NameAndAppearances on Character {name appearsIn}')
    doc('query DroidFieldInFragment {hero {name ...DroidFields}} fragment DroidFields on Droid {primaryFunction}')
    doc('query DroidFieldInFragment {hero {name ... on Droid {primaryFunction}}}')


    check('OperationDefinition', 'query { name }')
    check('OperationDefinition', '{ name }')
    check('VariableDefinitions', '($a: String)')
    check('OperationDefinition', 'query MyName($a: String) { name }')
    check('Argument', 'foo: 10')
    check('StringValue', '""')
    check('StringValue', '"foo"')
    check('StringValue', r'"foo\u0020bar"')
    check('StringValue', r'"foo\"bar"')
    check('BooleanValue', 'true')
    check('BooleanValue', 'false')
    check('Argument', 'foo: "bar"')
    check('ListValue', '[]')
    check('ListValue', '[   ]')

    verbose = True
    check('NullValue', 'null')
    check('Value', 'null')
    check('FractionalPart', '.456')
    check('ExponentPart', 'e20')
    check('ExponentPart', 'e-20')
    check('ExponentPart', 'e+20')
    check('Value', '$foo')
    check('Value', '123.0')
    check('FloatJustFrac', '123.456')
    check('Value', '123.456')
    check('Value', '123e20')
    check('Value', '123.456e20')
    check('Value', '0.456e20')
    check('ListValue', '[123, 1, null, "foo", true, null]')

    if allOkay: print("ALL OKAY!")
