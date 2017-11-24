type          := 'type' ws+ name #{ eol field* #}
name          := alpha+
field         := name arguments? #: field_type ws* eol
arguments     := '(' argument*  ')'
argument      := name #: field_type (#= default_value)?
field_type    := non_nullable | name | list
non_nullable  := (name | list) '!'
list          := '[' field_type ']'
default_value := int | string
int           := digit+
string        := '"' (!'"' any)* '"'
