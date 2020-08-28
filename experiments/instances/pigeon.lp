#const n=9.
pigeon(1..n+1). 
box(1..n).
1 { in(X,Y) : box(Y) } 1 :- pigeon(X).
:- 2 { in(X,Y) : pigeon(X) },  box(Y).
