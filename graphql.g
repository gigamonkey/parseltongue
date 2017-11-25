type          := 'type' ws+ type_name `{` eol field* `}`
type_name     := /[A-Z][A-Za-z]*/
name          := /[a-zA-Z]+/
field         := name arguments? `:` field_type ws* eol
arguments     := `(` argument* `)`
argument      := name `:` field_type (`=` default_value)?
field_type    := non_nullable | name | list
non_nullable  := (name | list) `!`
list          := `[` field_type `]`
default_value := int | string
int           := /[0-9]+/
string        := '"' (!'"' any)* '"'
eol           := u+000A
ws            := ' ' | u+0009
