MATCH (a)
MATCH (b)
WHERE elementId(a) < elementId(b)
RETURN count(*) AS pairs;