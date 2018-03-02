SELECT base.protocol,
hnd.date,
COALESCE(commit_count,0) AS commit_count,
COALESCE(star_count,0) AS star_count,
COALESCE(question_count,0) AS stack_question_count,
COALESCE(CASE WHEN base.protocol = 'Bitcoin' AND hnd.date <= '2018-03-01' THEN apc.post_count ELSE rp.post_count end,0) AS reddit_post_count,
COALESCE(rsubc.subscriber_count - rsubp.subscriber_count,0) AS reddit_subscriber_count,
COALESCE(tfc.follower_count - tfp.follower_count,0) AS twitter_follower_count,
COALESCE(story_count,0) AS hackernews_count,
COALESCE(search_interest,0) AS search_count,
COALESCE(close,0) AS price

FROM base_protocols base

LEFT JOIN 
(SELECT DISTINCT DATE FROM market_cap_volume WHERE DATE >= '2018-02-12') hnd
ON TRUE

LEFT JOIN github_stars gs
ON base.protocol = gs.protocol
AND hnd.date = gs.date

LEFT JOIN (
SELECT gci1.protocol, gci1.date,
CASE WHEN daily_commit_count IS NOT NULL THEN daily_commit_count
ELSE avg_commit_count 
END AS commit_count

FROM 
(SELECT base.protocol, hnd.date, week_date, commit_count
FROM base_protocols base
LEFT JOIN 
(SELECT DISTINCT DATE FROM market_cap_volume WHERE DATE >= '2018-02-12') hnd
ON TRUE
LEFT JOIN github_commits gc
ON base.protocol = gc.protocol
AND extract(week FROM hnd.date) = extract(week FROM week_date)
AND extract(YEAR FROM hnd.date) = extract(YEAR FROM week_date)) gci1

LEFT JOIN 
(SELECT protocol, week_date, cast(commit_count AS decimal)/7 AS daily_commit_count
FROM github_commits
WHERE week_date >= '2018-02-12') gci2
ON gci1.protocol = gci2.protocol
AND gci1.week_date = gci2.week_date

LEFT JOIN 
(SELECT protocol, avg(commit_count)/7 AS avg_commit_count
FROM github_commits
WHERE week_date >= '2018-02-12'
GROUP BY 1) gci3
ON gci1.protocol = gci3.protocol
) gc
ON base.protocol = gc.protocol
AND hnd.date = gc.date

LEFT JOIN stackoverflow_questions sc
ON base.protocol = sc.protocol
AND hnd.date = sc.date

LEFT JOIN reddit_posts rp
ON base.protocol = rp.protocol
AND hnd.date = rp.date

LEFT JOIN (
SELECT avg(post_count) AS post_count
FROM reddit_posts
WHERE protocol = 'Bitcoin') apc
ON base.protocol = rp.protocol

LEFT JOIN reddit_subscribers rsubp
ON base.protocol = rsubp.protocol
AND hnd.date - 1 = rsubp.date

LEFT JOIN reddit_subscribers rsubc
ON base.protocol = rsubc.protocol
AND hnd.date = rsubc.date

LEFT JOIN twitter_followers tfp
ON base.protocol = tfp.protocol
AND hnd.date - 1 = tfp.date

LEFT JOIN twitter_followers tfc
ON base.protocol = tfc.protocol
AND hnd.date = tfc.date

LEFT JOIN hackernews_stories hn
ON base.protocol = hn.protocol
AND hnd.date = hn.date

LEFT JOIN search_interest si
ON base.protocol = si.protocol
AND hnd.date = si.date

LEFT JOIN market_cap_volume mcv
ON base.protocol = mcv.protocol
AND hnd.date = mcv.date;