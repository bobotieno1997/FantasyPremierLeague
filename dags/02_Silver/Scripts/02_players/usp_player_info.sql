/*
    Stored Procedure: Update Silver Layer Players Info
    Purpose: Incrementally update silver.players_info with new records from bronze, preserving history
    Source: bronze.teams_info
    Target: silver.teams_info
*/


-- Create or replace the stored procedure
CREATE OR REPLACE PROCEDURE silver.usp_update_player_info()
LANGUAGE plpgsql
AS $$
BEGIN
    -- Purpose: Updates the silver.players_info table with new or changed player data from bronze.players_info
    -- Parameters: None
    -- Returns: None
    -- Exceptions: Captures and raises any errors during execution
    
    INSERT INTO silver.players_info (
        player_id,          -- Unique identifier for the player
        first_name,         -- Player's first name
        second_name,        -- Player's last name
        web_name,           -- Player's display name for web
        team_code,          -- Numeric code representing player's team
        team_id,            -- Identifier for player's team
        player_position,    -- Numeric code for player's position
        player_code,        -- Unique code for the player
        player_region,      -- Numeric code for player's region
        can_select,         -- Flag indicating if player can be selected
        photo_url,          -- URL to player's photo
        dwh_team_id,        -- Data warehouse team identifier (team_id + years)
        dwh_player_id       -- Data warehouse player identifier (player_id + years)
    )
    SELECT
        CAST(bpi.player_id AS BIGINT) AS player_id,
        bpi.first_name,
        bpi.second_name,
        bpi.web_name,
        CAST(bpi.team_code AS INT) AS team_code,
        CAST(bpi.team_id AS INT) AS team_id,
        CAST(bpi.player_position AS INT) AS player_position,
        CAST(bpi.player_code AS INT) AS player_code,
        CAST(bpi.region AS INT) AS player_region,  -- Region code mapped to player_region
        bpi.can_select,
        bpi.photo_url,
        -- Construct DWH team ID by concatenating team_id with min and max kickoff years
        CAST(CONCAT(
            bpi.team_id,
            EXTRACT(YEAR FROM bpi.min_kickoff::TIMESTAMP),
            EXTRACT(YEAR FROM bpi.max_kickoff::TIMESTAMP)
        ) AS BIGINT) AS dwh_team_id,
        -- Construct DWH player ID by concatenating player_id with min and max kickoff years
        CAST(CONCAT(
            bpi.player_id,
            EXTRACT(YEAR FROM bpi.min_kickoff::TIMESTAMP),
            EXTRACT(YEAR FROM bpi.max_kickoff::TIMESTAMP)
        ) AS BIGINT) AS dwh_player_id
    FROM bronze.players_info bpi
    LEFT JOIN silver.players_info spi 
        ON spi.dwh_team_id = CAST(CONCAT(
            bpi.team_id,
            EXTRACT(YEAR FROM bpi.min_kickoff::TIMESTAMP),
            EXTRACT(YEAR FROM bpi.max_kickoff::TIMESTAMP)
        ) AS BIGINT)
        AND spi.dwh_player_id = CAST(CONCAT(
            bpi.player_id,
            EXTRACT(YEAR FROM bpi.min_kickoff::TIMESTAMP),
            EXTRACT(YEAR FROM bpi.max_kickoff::TIMESTAMP)
        ) AS BIGINT)
    WHERE spi.dwh_team_id IS NULL OR spi.dwh_player_id IS NULL  -- Only insert new records
    ORDER BY bpi.player_id ASC;  -- Ensure consistent ordering by player_id

EXCEPTION
    WHEN OTHERS THEN
        -- Capture and raise detailed error information
        RAISE NOTICE 'Error in usp_update_player_info: %', SQLERRM;
        RAISE NOTICE 'Error State: %', SQLSTATE;
        RAISE EXCEPTION 'Failed to update player info: %', SQLERRM;
END;
$$;

