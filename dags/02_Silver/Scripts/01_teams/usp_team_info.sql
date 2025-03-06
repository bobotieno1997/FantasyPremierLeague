/*
    Stored Procedure: Update Silver Layer Teams Info
    Purpose: Incrementally update silver.teams_info with new records from bronze, preserving history
    Source: bronze.teams_info
    Target: silver.teams_info
*/


-- Create or replace the stored procedure
CREATE OR REPLACE PROCEDURE silver.usp_update_team_info()
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE '=======================================';
    RAISE NOTICE 'Update silver.teams_info table';
    RAISE NOTICE '=======================================';

    -- Insert new team records into silver layer
    -- Business Rule: Only adds records not already present in silver based on team_code
        INSERT INTO silver.teams_info(
        team_id,team_code,team_name,team_short_name,dwh_team_id
        )
        SELECT 
            CAST(bti.team_id AS SMALLINT)AS team_id,
            CAST(bti.team_code AS SMALLINT) AS team_code,
            bti.team_name,
            bti.team_short_name,
            CAST(
            CONCAT(bti.team_id,
            EXTRACT(YEAR FROM bti.min_kickoff::TIMESTAMP),
            EXTRACT(YEAR FROM bti.max_kickoff::TIMESTAMP)) AS BIGINT)AS dwh_team_id
        FROM bronze.teams_info bti 
        LEFT JOIN silver.teams_info sti ON sti.dwh_team_id = CAST(CONCAT(bti.team_id,
        EXTRACT(YEAR FROM bti.min_kickoff::TIMESTAMP),
        EXTRACT(YEAR FROM bti.max_kickoff::TIMESTAMP)) AS BIGINT)
        WHERE sti.dwh_team_id IS NULL;

    -- Success message
    RAISE NOTICE '=======================================';
    RAISE NOTICE 'Updated silver.teams_info table successfully';
    RAISE NOTICE '=======================================';

EXCEPTION
    WHEN OTHERS THEN
        -- Error handling: Log the error message
        RAISE NOTICE 'ERROR: %', SQLERRM;
        RAISE;  -- Re-raise the exception after logging
END;
