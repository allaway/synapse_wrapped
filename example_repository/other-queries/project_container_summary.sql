-- For monitoring and especially when the master fileview is broken, 
-- we use this to get list of projects and their container (folder) count from largest to smallest
-- to maintain a working fileview configuration

USE ROLE DATA_ANALYTICS;
USE WAREHOUSE COMPUTE_XSMALL;
USE DATABASE SYNAPSE_DATA_WAREHOUSE;
USE SCHEMA SYNAPSE;

WITH fileview_scope AS (
    -- Retrieve the list of project IDs from the master fileview
    SELECT
        CAST(scopes.value AS INTEGER) AS project_id
    FROM
        synapse_data_warehouse.synapse.node_latest,
        LATERAL FLATTEN(input => node_latest.scope_ids) scopes
    WHERE
        id = 16858331 -- the master fileview
),
node_folders AS (
    
    SELECT
        nl.id,
        nl.parent_id,
        nl.node_type,
        fs.project_id
    FROM
        synapse_data_warehouse.synapse.node_latest nl
    JOIN
        fileview_scope fs ON nl.project_id = fs.project_id
    WHERE
        nl.node_type = 'folder'
)
SELECT
    nf.project_id,
    COUNT(DISTINCT nf.id) AS total_folders
FROM
    node_folders nf
GROUP BY
    nf.project_id
ORDER BY
    total_folders DESC;
