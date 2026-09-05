---
status: Active
title: 'Write code that reads like the code around it'
version: 1
tags: [economy]
date: '2026-09-05'
surface: [repository]
grounds: VALUE-006
summary: >-
  Match the surrounding comment density, naming and idiom. Code is read far
  more often than it is written, and a patch in a personal dialect charges
  every future reader for the switch — including the reader who has to decide
  which convention the file now follows.
---

# PRACTICE-007: Write code that reads like the code around it

A file has a dialect: how densely it comments, how it names things, which of
several correct constructions it reaches for. That dialect is not decoration.
It is what lets someone skim the file and find the part they need, and a patch
written in a different one costs every subsequent reader the switch.

The cost compounds in a way a single diff hides. Two dialects in one file leave
the next contributor with a question the file no longer answers — which one is
this project's? — and the usual resolution is a third. What began as a stylistic
preference becomes a file nobody can skim.

So the local convention wins over the better convention, absent a reason to
change it. Where the surrounding style really is wrong, that is a change worth
making deliberately and saying out loud, across the file rather than in the one
function being touched. Silently correcting it in a patch about something else
produces the mixed file rather than the improved one.
