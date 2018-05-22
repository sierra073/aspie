/* 
1. update protocols.csv input data
2. run get_data.sh first
3. run this
4. run get_data.sh again
*/

INSERT INTO base_protocols VALUES
('Numeraire');

INSERT INTO protocols_sentiment VALUES
('Numeraire',current_date);

UPDATE  twitter_followers
SET DATE = CURRENT_DATE
WHERE protocol='Numeraire';

UPDATE  reddit_posts
SET DATE = CURRENT_DATE
WHERE protocol='Numeraire';

UPDATE  reddit_subscribers
SET DATE = CURRENT_DATE
WHERE protocol='Numeraire';

/*hackernews = automatic, starting current day*/

UPDATE  search_interest
SET DATE = CURRENT_DATE - INTERVAL '7 day'
WHERE protocol='Numeraire';

UPDATE  stackoverflow_questions
SET DATE = '2017-01-01'::DATE
WHERE protocol='Numeraire';

UPDATE  github_commits 
SET week_date = CURRENT_DATE - INTERVAL '12 month' - INTERVAL '7 day'
WHERE protocol='Numeraire';

INSERT INTO github_stars VALUES
('Numeraire',''::date,0);

INSERT INTO market_cap_volume VALUES
('Numeraire','2017-01-01'::date);
