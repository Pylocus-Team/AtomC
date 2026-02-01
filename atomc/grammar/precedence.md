# Rynx 2.0 Operator Precedence and Associativity

1. () [] function call, subscript — L
2. ! - unary — R
3. * / % — L
4. + - — L
5. < > <= >= == != — L
6. && — L
7. || — L
8. = assignment — R (statement-level, not in expression)

Expression precedence (low to high):
logical_or → logical_and → comparison → term (+ -) → factor (* / %) → unary → primary
