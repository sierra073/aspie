SELECT 

s.protocol,
s.date, 
s.close AS price
FROM market_cap_volume s
WHERE s.date BETWEEN '2017-01-01' AND CURRENT_DATE

UNION

SELECT 
'index' AS protocol,
c.date, 
c.price
FROM cbi_data c
WHERE c.date BETWEEN '2017-01-01' AND (SELECT MAX(date) FROM market_cap_volume)

ORDER BY date, protocol;