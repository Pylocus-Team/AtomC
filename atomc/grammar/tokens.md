# Rynx 2.0 Token Definitions

## Keywords
start, end, task, when, else, loop, thru, each, in, match, case, flow, break, return, let, guess, block, step

## Type keywords
num, dec, text, yes, nums, texts, decs, yess

## Literals
- number: optional minus, digits, optional decimal part
- string_literal: " ... " with escaped \" \\ \n \t
- true, false

## Operators
- Arithmetic: + - * / %
- Comparison: < > <= >= == !=
- Logical: && || !
- Range: ..
- Assignment: =

## Delimiters
{ } ( ) [ ] , ; :

## Identifier
letter (letter | digit | _)*

## Comments (skipped by lexer)
// line
/* block */

## Token attributes (mandatory)
- kind
- value (for literals/identifiers)
- line (1-based)
- column (1-based)
- end_column (for underline)
