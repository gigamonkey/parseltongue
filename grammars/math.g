TOKENS: '+' '(' ')' '*' number
WHITESPACE: /\s+/

expression    := term ('+' expression)?
parenthesized := ~'(' expression ~')'
factor        := parenthesized | number
term          := factor ('*' term)?
number        := /[0-9]*/
