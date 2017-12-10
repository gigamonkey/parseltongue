# Munged from a direct transliteration of the grammar from
# http://facebook.github.io/graphql/October2016/

TOKENS: '!' '$' '(' ')' '...' ':' '=' '@' '[' ']' '{' '|' '}' Name IntValue FloatValue StringValue BooleanValue NullValue EnumValue
WHITESPACE: Ignored

SourceCharacter     := /[\u0009\u000A\u000D\u0020-\uFFFF]/
UnicodeBOM          := u+feff
WhiteSpace          := u+0009 | u+0020
LineTerminator      := u+000A | u+000D !u+000A | u+000D u+000A
Comment             := '#' commentChar*
CommentChar         := !lineTerminator sourceCharacter
Comma               := ','
Ignored             := UnicodeBOM | WhiteSpace | LineTerminator | Comment | Comma
Punctuator          := '!' | '$' | '(' | ')' | '...' | ':' | '=' | '@' | '[' | ']' | '{' | '|' | '}'
Name                := /[_A-Za-z][_0-9A-Za-z]*/
Document            := Definition+
Definition          := OperationDefinition | FragmentDefinition
OperationDefinition := NamedOperation | AnonymousQuery
NamedOperation      := OperationType Name? VariableDefinitions? Directives? SelectionSet
AnonymousQuery      := SelectionSet
OperationType       := 'query' | 'mutation' | 'subscription'
SelectionSet        := ~'{' Selection+ ~'}'
Selection           := Field | FragmentSpread | InlineFragment
Field               := Alias? Name Arguments? Directives? SelectionSet?
Arguments           := ~'(' Argument+ ~')'
Argument            := Name ~':' Value
Alias               := Name ~':'
FragmentSpread      := ~'...' FragmentName Directives?
FragmentDefinition  := ~'fragment' FragmentName TypeCondition Directives? SelectionSet
FragmentName        := !'on' Name
TypeCondition       := 'on' NamedType
InlineFragment      := ~'...' TypeCondition? Directives? SelectionSet
Value               := Variable | FloatValue | IntValue | StringValue | BooleanValue | NullValue | EnumValue | ListValue | ObjectValue
IntValue            := IntegerPart
IntegerPart         := Zero | NonZero
Zero                := NegativeSign? '0'
NonZero             := NegativeSign? NonZeroDigit Digit*
NegativeSign        := '-'
Digit               := /[0-9]/
NonZeroDigit        := !'0' Digit
FloatValue          := IntegerPart (FractionalPart | implicit(0)) (ExponentPart | (implicit(+) implicit(0)))
FractionalPart      := ~'.' Digit+
ExponentPart        := ~ExponentIndicator (Sign | implicit(+)) Digit+
ExponentIndicator   := 'e' | 'E'
Sign                := '+' | '-'
BooleanValue        := 'true' | 'false'
StringValue         := ~'"' StringCharacter* ~'"'
StringCharacter     := !('"' | '\' | LineTerminator) SourceCharacter | ~'\u' EscapedUnicode | ~'\' EscapedCharacter
EscapedUnicode      := /[0-9A-Fa-f]{4}/
EscapedCharacter    := '"' | '\' | '/' | 'b' | 'f' | 'n' | 'r' | 't'
NullValue           := 'null'
EnumValue           := !(NullValue | BooleanValue) Name
ListValue           := ~'[' Value* ~']'
ObjectValue         := ~'{' ObjectField* ~'}'
ObjectField         := Name ~':' Value
Variable            := ~'$' Name
VariableDefinitions := ~'(' VariableDefinition+ ~')'
VariableDefinition  := Variable ~':' Type DefaultValue?
DefaultValue        := Value
Type                := NonNullType | ListType | NamedType
NamedType           := Name
ListType            := ~'[' Type ~']'
NonNullType         := NamedType ~'!' | ListType ~'!'
Directives          := Directive+
Directive           := ~'@' Name Arguments?
