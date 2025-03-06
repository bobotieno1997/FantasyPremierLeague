-- Data quality checks for bronze.teams_info
-- Identified duplicate and null values in int fields
SELECT 
    team_id,
    team_code,
    COUNT(*)
FROM silver.teams_info
WHERE team_id IS NULL OR team_code IS NULL
GROUP BY team_id, team_code
HAVING COUNT(*) > 1;


-- Identifies null and values with extra space
select
distinct 
team_name,
team_short_name
from silver.teams_info
where team_name <> TRIM(team_name) or 
team_short_name <> TRIM(team_short_name)
or team_name is null or team_short_name is null

-- Identifies duplicate values in text field
select
team_name,
team_short_name,
count(*)
from silver.teams_info
group by team_name, team_short_name
having count(*)> 1