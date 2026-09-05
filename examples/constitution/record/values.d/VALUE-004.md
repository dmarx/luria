---
status: Active
title: 'A record that cannot be checked will drift, and the drift is invisible'
version: 1
tags: [record]
date: '2026-09-05'
summary: >-
  Documentation governed by prose alone rots silently: the machinery keeps
  working while the instructions stop being true. Whatever a record asserts,
  something should be able to fail on it.
---

# VALUE-004: A record that cannot be checked will drift, and the drift is invisible

The failure mode is not that the docs are wrong on the day they are written.
It is that nothing exercises them afterwards, so they stay plausible while
becoming false — and the moment of discovery is someone following the
instructions and finding they do not work.

This is why a worked example beats a documented one. A configuration block in
a guide is a claim nobody runs. The same block, built and linted in CI, is a
claim that fails the day it stops being true.

It applies to this record. These documents describe an assistant's operating
constitution; the machinery cannot check whether the description is *faithful*,
and saying so is part of being honest about what the check covers. What it can
check is internal: that every practice names a value, that every override
resolves, that the views match their sources. Those are the parts a reader can
rely on without taking anyone's word.
