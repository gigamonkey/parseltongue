#!/usr/bin/env python3

from parseltongue import TextInput
from parseltongue import parse
from peg import grammar


class Operation:

    pass


class NamedOperation(Operation):
    def __init__(self, args):
        type, name, vars, directives, selection_set = args
        self.type = type
        self.name = name
        self.vars = vars
        self.directives = directives
        self.selection_set = selection_set


class AnonymousQuery(Operation):
    def __init__(self, selection_set):
        self.type = "query"
        self.name = None
        self.vars = None
        self.directives = None
        self.selection_set = selection_set


class Field:
    def __init__(self, args):
        alias, name, arguments, directives, selection_set = args
        self.alias = alias
        self.name = name
        self.arguments = arguments
        self.directives = directives
        self.selection_set = selection_set


class Argument:
    def __init__(self, args):
        name, value = args
        self.name = name
        self.value = value


class FragmentDefinition:
    def __init__(self, args):
        name, type_condition, directives, selection_set = args
        self.name = name
        self.type_condition = type_condition
        self.directives = directives
        self.selection_set = selection_set


class FragmentSpread:
    def __init__(self, args):
        name, directives = args
        self.name = name
        self.directives = directives


class InlineFragment:
    def __init__(self, args):
        type_condition, directives, selection_set = args
        self.type_condition = type_condition
        self.directives = directives
        self.selection_set = selection_set


class Variable:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Variable({})".format(self.name)


class VariableDefinition:
    def __init__(self, args):
        variable, type, default = args
        self.variable = variable
        self.type = type
        self.default = default


class NamedType:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "NamedType({})".format(self.name)


class ListType:
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "ListType({})".format(self.type)


class NonNullType:
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "NonNullType({})".format(self.type)


class Directive:
    def __init__(self, args):
        name, arguments = args
        self.name = name
        self.arguments = arguments


class EnumValue:
    def __init__(self, name):
        self.name = name


def identity(x):
    return x


def text(args):
    return "".join(x for x in args if x is not None)


def value(x):
    return lambda args: x


def to_dict(*fields):
    return lambda args: {k: v for k, v in zip(fields, args) if k is not None}


def non_zero(args):
    negsign, d1, ds = args
    n = int("{}{}".format(d1, "".join(ds)))
    return n if negsign is None else -n


def make_float(args):
    i, f, (s, e) = args
    return float("{}.{}e{}{}".format(i, text(f), s, text(e)))


def make_bool(arg):
    return arg == "true"


def escaped_unicode(arg):
    return chr(int(arg, 16))


x = {
    "AnonymousQuery": AnonymousQuery,
    "Argument": Argument,
    "BooleanValue": make_bool,
    "Directive": Directive,
    "EnumValue": EnumValue,
    "EscapedUnicode": escaped_unicode,
    "Field": Field,
    "FloatValue": make_float,
    "FragmentDefinition": FragmentDefinition,
    "FragmentSpread": FragmentSpread,
    "InlineFragment": InlineFragment,
    "ListType": ListType,
    "NamedOperation": NamedOperation,
    "NamedType": NamedType,
    "NonNullType": NonNullType,
    "NonZero": non_zero,
    "NullValue": value(None),
    "ObjectField": tuple,
    "StringValue": text,
    "Variable": Variable,
    "VariableDefinition": VariableDefinition,
    "Zero": value(0),
}


g = grammar("grammars/query.g").bindings(x)


if __name__ == "__main__":

    import parseltongue

    parseltongue.verbose = False

    verbose = False

    allOkay = True

    def check(rule, text):
        parseltongue.verbose = False
        ok, _, r = parse(g, rule, TextInput(text))
        if ok:
            if verbose:
                print("ok: {} parsed {} => {}".format(rule, repr(text), r))
        else:
            print("FAIL: {} did not parse {}".format(rule, repr(text)))
            parseltongue.verbose = True
            parse(g, rule, TextInput(text))

    def doc(text):
        check("Document", text)

    # Specific rules
    check("Name", "name")
    check("Field", "hero { name }")
    check("Field", "name")
    check("SelectionSet", "{name}")
    check("WhiteSpace", " ")
    check("SelectionSet", "{ name }")
    check("OperationType", "query")
    check("Name", "HeroNameQuery")
    check("SelectionSet", "{ hero { name } }")
    check("SelectionSet", "{\nhero { name } }")
    check("StringValue", '"1000"')
    check("Value", '"1000"')
    check("Arguments", '(id: "1000")')
    check("Field", 'human(id: "1000")')
    check("VariableDefinition", "$someId: String!")
    check("VariableDefinitions", "($someId: String)")
    check("NonNullType", "String!")
    check("VariableDefinitions", "($someId: String!)")

    # From https://github.com/graphql/graphql-js/blob/master/src/__tests__/starWarsQuery-test.js
    doc("query HeroNameQuery { hero { name } }")
    doc("query HeroNameQuery { hero { name,title } }")
    doc("query { hero { name } }")
    doc("{ hero { name } }")
    doc("query HeroNameAndFriendsQuery {hero {id name friends {name}}}")
    doc("query HeroNameAndFriendsQuery {\n          hero {\n            id\n            name\n            friends {\n              name\n            }\n          }\n        }\n")
    doc(
        "query NestedQuery {\n          hero {\n            name\n            friends {\n              name\n              appearsIn\n              friends {\n                name\n              }\n            }\n          }\n        }"
    )
    doc('query FetchLukeQuery {human(id: "1000") {name}}')
    doc("query FetchSomeIDQuery($someId: String!) { human(id: $someId) {name} }")
    doc('query FetchLukeAliased {luke: human(id: "1000") {name}}')
    doc('query FetchLukeAndLeiaAliased {luke: human(id: "1000") {name} leia: human(id: "1003") {name}}')
    doc('query DuplicateFields {luke: human(id: "1000") {name homePlanet} leia: human(id: "1003") {name homePlanet}}')
    doc('query UseFragment {luke: human(id: "1000") {...HumanFragment} leia: human(id: "1003") {...HumanFragment}} fragment HumanFragment on Human {name homePlanet}')
    doc("query CheckTypeOfR2 {hero {__typename name}}")
    doc("query CheckTypeOfLuke {hero(episode: EMPIRE) {__typename name}}")
    doc("query HeroNameQuery {hero {name secretBackstory}}")
    doc("query HeroNameQuery {hero {name friends {name secretBackstory}}}")
    doc("query HeroNameQuery {mainHero: hero {name story: secretBackstory}}")

    # From https://github.com/graphql/graphql-js/blob/master/src/__tests__/starWarsValidation-test.js
    doc(
        "query NestedQueryWithFragment {hero {...NameAndAppearances friends {...NameAndAppearances friends {...NameAndAppearances}}}} fragment NameAndAppearances on Character {name appearsIn}"
    )
    doc("query DroidFieldInFragment {hero {name ...DroidFields}} fragment DroidFields on Droid {primaryFunction}")
    doc("query DroidFieldInFragment {hero {name ... on Droid {primaryFunction}}}")

    check("OperationDefinition", "query { name }")
    check("OperationDefinition", "{ name }")
    check("VariableDefinitions", "($a: String)")
    check("OperationDefinition", "query MyName($a: String) { name }")
    check("Argument", "foo: 10")
    check("StringValue", '""')
    check("StringValue", '"foo"')
    check("StringValue", r'"foo\u0020bar"')
    check("StringValue", r'"foo\"bar"')
    check("BooleanValue", "true")
    check("BooleanValue", "false")
    check("Argument", 'foo: "bar"')
    check("ListValue", "[]")
    check("ListValue", "[   ]")

    check("NullValue", "null")
    check("Value", "null")
    check("FractionalPart", ".456")
    check("ExponentPart", "e20")
    check("ExponentPart", "e-20")
    check("ExponentPart", "e+20")
    check("Value", "$foo")
    check("Value", "123.0")
    verbose = True
    check("FloatValue", "123.456")
    check("Value", "123.456")
    check("Value", "123e20")
    check("Value", "123.456e20")
    check("Value", "0.456e20")
    check("ListValue", '[123, 1, null, "foo", true, null]')

    if allOkay:
        print("ALL OKAY!")
