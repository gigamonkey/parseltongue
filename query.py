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

    def doc(text):
        check('Document', text)


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
