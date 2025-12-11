-- In NF related project, this returns a table of percentage of valid or missing institution in a table

-- Part 0: Setup
USE ROLE DATA_ANALYTICS;
USE WAREHOUSE COMPUTE_XSMALL;
USE DATABASE SYNAPSE_DATA_WAREHOUSE;
USE SCHEMA SYNAPSE;

-- Step 1: Extract NF Project IDs
WITH nf_project_scope AS (
    SELECT
        CAST(scopes.value AS INTEGER) AS scope_id
    FROM
        synapse_data_warehouse.synapse.node_latest,
        LATERAL FLATTEN(input => node_latest.scope_ids) scopes
    WHERE
        id = 52677631
),

-- Step 2: Align PI Emails with NF Projects
project_nodes AS (
    SELECT
        nl.id AS project_id,
        nl.name AS project_name,
        nl.created_by AS pi_user_id,
        up.email AS pi_email,
        COALESCE(up.company, up.location) AS pi_institution
    FROM
        synapse_data_warehouse.synapse.node_latest nl
    LEFT JOIN
        synapse_data_warehouse.synapse.userprofile_latest up
        ON nl.created_by = up.id
    WHERE
        nl.node_type = 'project'
),

-- Step 3: Flag Issues
flagged_projects AS (
    SELECT
        pn.project_id,
        pn.project_name,
        pn.pi_user_id,
        pn.pi_email,
        pn.pi_institution,
        CASE
            WHEN pn.pi_email IS NULL THEN 'Missing Email'
            WHEN pn.pi_institution IS NULL THEN 'Missing Institution'
            WHEN LOWER(pn.pi_institution) LIKE '%unknown%' OR LOWER(pn.pi_institution) LIKE '%n/a%' THEN 'Unclear Institution'
            ELSE 'Valid'
        END AS issue_type
    FROM
        project_nodes pn
    JOIN
        nf_project_scope nps
    ON
        pn.project_id = nps.scope_id
)

-- Step 4: Aggregate Results into a Summary Table
SELECT
    issue_type,
    COUNT(*) AS count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS percentage
FROM
    flagged_projects
GROUP BY
    issue_type
ORDER BY
    count DESC;
