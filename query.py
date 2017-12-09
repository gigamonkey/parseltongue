#!/usr/bin/env python3

from parseltongue import *
from peg import grammar

g = grammar('query.g')

if __name__ == '__main__':

    import parseltongue

    parseltongue.verbose = False

    def check(rule, text):
        parseltongue.verbose = False
        ok, _, r = parse(g, rule, TextInput(text))
        if ok:
            print('ok: {} parsed {} => {}'.format(rule, repr(text), r))
        else:
            print('FAIL: {} did not parse {}'.format(rule, repr(text)))
            parseltongue.verbose = True
            parse(g, rule, TextInput(text))

    def opd(text):
        check('OperationDefinition', text)


    # Specific rules
    check('Field', 'hero { name }')
    check('Name', 'name')
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

    # Top level. Examples takesn from https://github.com/graphql/graphql-js/blob/master/src/__tests__/starWarsQuery-test.js
    opd('query HeroNameQuery { hero { name } }')
    opd('query HeroNameQuery { hero { name,title } }')
    opd('query { hero { name } }')
    opd('{ hero { name } }')
    opd('query HeroNameAndFriendsQuery {hero {id name friends {name}}}')
    opd('query HeroNameAndFriendsQuery {\n          hero {\n            id\n            name\n            friends {\n              name\n            }\n          }\n        }\n')
    opd('query NestedQuery {\n          hero {\n            name\n            friends {\n              name\n              appearsIn\n              friends {\n                name\n              }\n            }\n          }\n        }')
    opd('query FetchLukeQuery {human(id: "1000") {name}}')
    opd('query FetchSomeIDQuery($someId: String!) { human(id: $someId) {name} }')
    opd('query FetchLukeAliased {luke: human(id: "1000") {name}}')
    opd('query FetchLukeAndLeiaAliased {luke: human(id: "1000") {name} leia: human(id: "1003") {name}}')
    opd('query DuplicateFields {luke: human(id: "1000") {name homePlanet} leia: human(id: "1003") {name homePlanet}}')
    opd('query UseFragment {luke: human(id: "1000") {...HumanFragment} leia: human(id: "1003") {...HumanFragment}} fragment HumanFragment on Human {name homePlanet}')
    opd('query CheckTypeOfR2 {hero {__typename name}}')
    opd('query CheckTypeOfLuke {hero(episode: EMPIRE) {__typename name}}')
    opd('query HeroNameQuery {hero {name secretBackstory}}')
    opd('query HeroNameQuery {hero {name friends {name secretBackstory}}}')
    opd('query HeroNameQuery {mainHero: hero {name story: secretBackstory}}')
