#!/usr/bin/env python3

from parseltongue import TextInput, match, star, text

if __name__ == '__main__':

    digit    = match(str.isdigit)
    number   = text(star(digit)).returning(int)
    ws       = star(match(str.isspace)).returning(None)
    plus     = text(ws.then('+').then(ws))
    addition = number.then(plus).then(number)

    input = TextInput('1234 + 4567')

    ok, _, r = addition.match(input)
    print(r if ok else 'Parse failed')
