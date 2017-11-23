#!/usr/bin/env python3

from parseltongue import TextInput, literal, match, star, text

if __name__ == '__main__':

    p = {}

    p['digit']    = match(str.isdigit)
    p['number']   = text(star('digit')).returning(int)
    p['ws']       = star(match(str.isspace)).returning(None)
    p['plus']     = text(match('ws').then(literal('+')).then('ws'))
    p['addition'] = match('number').then('plus').then('number')

    input = TextInput('1234 + 4567')

    ok, _, r = p['addition'].match(p, input)
    print(r if ok else 'Parse failed')
