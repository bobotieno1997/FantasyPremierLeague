-- Creates or replaces a view in the gold schema for player statistics facts with dimensional references
CREATE OR REPLACE VIEW gold_v_dimension_season
AS
SELECT 
    DISTINCT
    CONCAT(
        LEFT(season::text,4), '/', RIGHT(season::text,4)) as season_name,
    season 
FROM silver.games_info
ORDER BY season ASC;