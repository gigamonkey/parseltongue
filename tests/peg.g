a := rule
b := rule+
c := rule*
d := rule?
e := &rule
f := !rule
g := a b
h := a | b
i := a | b c | d
j := a* | b
k := '\u000d'
l := u+000d !u+000a
m := u+000a | u+000d !u+000a | u+000d u+000a
n := 'foo'
o := 'foo' 'bar'
p := 'foo' | 'bar'
q := !a b
r := `!`
s := (a | b)
t := (a | b) `!`
u := !(a | b)
v := !(a+)
