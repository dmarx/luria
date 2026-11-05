-- experiments/duckdb_pgq/rules.sql
-- luria/logic/relations.lp and invariants.lp, rule for rule, as SQL views.
-- Expects the fact tables from load.py and a table pattern_edge(a0 name,
-- a1 first, a2 last), empty when the record declares no patterns.

-- ── relations.lp ─────────────────────────────────────────────────────────
CREATE VIEW reads AS
SELECT DISTINCT d.a1 AS s, rv.a1 AS f, rv.a0 AS c, rv.a2 AS x
FROM doc d
JOIN ref_value rv ON rv.a0 = d.a0
JOIN ref_target rt ON rt.a0 = d.a1 AND rt.a1 = rv.a1
JOIN doc dx ON dx.a0 = rv.a2 AND dx.a1 = rt.a2;

CREATE VIEW held AS
SELECT s, f, c, x FROM reads
UNION
SELECT rc.a0, rc.a1, r.x, r.c
FROM ref_converse rc
JOIN ref_target rt ON rt.a0 = rc.a0 AND rt.a1 = rc.a1
JOIN reads r ON r.s = rt.a2 AND r.f = rc.a2
JOIN doc d ON d.a0 = r.x AND d.a1 = rc.a0;

-- ── invariants.lp: a relation's own invariant ────────────────────────────
CREATE VIEW rel_pair AS
SELECT DISTINCT h.s, h.f, least(h.c, h.x) AS a, greatest(h.c, h.x) AS b
FROM held h WHERE EXISTS (SELECT 1 FROM ref_invariant ri
                          WHERE ri.a0 = h.s AND ri.a1 = h.f);

CREATE VIEW unbound_relation AS
SELECT p.* FROM rel_pair p
WHERE NOT EXISTS (
  SELECT 1 FROM ref_invariant ri
  JOIN holds ha ON ha.a0 = p.a AND ha.a1 = ri.a2
  JOIN holds hb ON hb.a0 = p.b AND hb.a1 = ri.a2 AND hb.a2 = ha.a2
  WHERE ri.a0 = p.s AND ri.a1 = p.f);

-- ── a chain's invariant: every edge it walks ─────────────────────────────
CREATE VIEW walks AS
SELECT a0 AS n, a1 AS f FROM chain_relation
UNION SELECT a0, a1 FROM chain_sibling;

CREATE VIEW near1 AS
SELECT DISTINCT c.a0 AS n, h.c AS a, h.x AS b
FROM chain c
JOIN chain_invariant ci ON ci.a0 = c.a0
JOIN walks w ON w.n = c.a0
JOIN held h ON h.s = c.a1 AND h.f = w.f
JOIN doc da ON da.a0 = h.c AND da.a1 = c.a1
JOIN doc db ON db.a0 = h.x AND db.a1 = c.a1
UNION
SELECT DISTINCT c.a0, pe.a1, pe.a2
FROM chain c
JOIN chain_invariant ci ON ci.a0 = c.a0
JOIN walks w ON w.n = c.a0
JOIN pattern_edge pe ON pe.a0 = w.f
JOIN doc da ON da.a0 = pe.a1 AND da.a1 = c.a1
JOIN doc db ON db.a0 = pe.a2 AND db.a1 = c.a1;

CREATE VIEW near AS
SELECT n, a, b FROM near1 UNION SELECT n, b, a FROM near1;

CREATE VIEW chain_pair AS
SELECT DISTINCT n, a, b FROM near WHERE a <= b;

CREATE VIEW unbound_edge AS
SELECT p.* FROM chain_pair p
WHERE NOT EXISTS (
  SELECT 1 FROM chain_invariant ci
  JOIN holds ha ON ha.a0 = p.a AND ha.a1 = ci.a1
  JOIN holds hb ON hb.a0 = p.b AND hb.a1 = ci.a1 AND hb.a2 = ha.a2
  WHERE ci.a0 = p.n);

-- ── and the line ─────────────────────────────────────────────────────────
-- reach is a transitive closure; UNION (not UNION ALL) is what makes the
-- recursion stop, as set semantics does in clingo.
CREATE VIEW reach AS
WITH RECURSIVE r(n, a, c) AS (
  SELECT DISTINCT n, a, a FROM near
  UNION
  SELECT r.n, r.a, nr.b FROM r JOIN near nr ON nr.n = r.n AND nr.a = r.c)
SELECT * FROM r;

CREATE VIEW member AS
SELECT n, min(c) AS r, a FROM reach GROUP BY n, a;

-- clingo: #count { M : member(N, R, M), not holds(M, I, V) } = 0, for a
-- value V the root holds. Written as a count over a join, not as a doubly
-- nested correlated NOT EXISTS: DuckDB 1.5.6 returns wrong rows for the
-- nested form (302 correct, 308 returned on this record; 2.0.0 is right).
CREATE VIEW common AS
WITH candidate AS (
  SELECT DISTINCT m.n, m.r, ci.a1 AS i, hr.a2 AS v
  FROM member m
  JOIN chain_invariant ci ON ci.a0 = m.n
  JOIN holds hr ON hr.a0 = m.r AND hr.a1 = ci.a1
  WHERE m.a = m.r),
size AS (SELECT n, r, count(*) AS k FROM member GROUP BY n, r),
holding AS (
  SELECT c.n, c.r, c.v, count(DISTINCT m.a) AS k
  FROM candidate c
  JOIN member m ON m.n = c.n AND m.r = c.r
  JOIN holds h ON h.a0 = m.a AND h.a1 = c.i AND h.a2 = c.v
  GROUP BY c.n, c.r, c.v)
SELECT DISTINCT h.n, h.r FROM holding h
JOIN size s ON s.n = h.n AND s.r = h.r
WHERE h.k = s.k;

CREATE VIEW unbound_line AS
SELECT n, r FROM member WHERE a = r
EXCEPT
SELECT n, r FROM common;
