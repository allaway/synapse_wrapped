USE ROLE DATA_ANALYTICS;
USE WAREHOUSE COMPUTE_XSMALL;
USE DATABASE SYNAPSE_DATA_WAREHOUSE;
USE SCHEMA SYNAPSE;

-- 1) Get NF Project IDs
WITH nf_project_scope AS (
    SELECT
        CAST(scopes.value AS INTEGER) AS scope_id
    FROM
        synapse_data_warehouse.synapse.node_latest,
        LATERAL FLATTEN(input => node_latest.scope_ids) scopes
    WHERE
        id = 52677631
),

-- 2) Flatten the effective_ars array to extract each AR ID
nf_projects_with_ar AS (
    SELECT
        nl.id AS entity_id,
        CAST(ar.value AS INTEGER) AS ar_id
    FROM
        synapse_data_warehouse.synapse.node_latest nl
        JOIN nf_project_scope nps ON nl.id = nps.scope_id
        CROSS JOIN LATERAL FLATTEN(input => nl.effective_ars) ar
)

-- 3) Join AR IDs to accessrequirement_latest for requirement details
SELECT
    p.entity_id,
    a.id AS ar_id,
    a.name AS ar_name,
    a.is_duc_required,
    a.is_irb_approval_required,
    a.is_idu_required,
    a.is_certified_user_required,
    a.is_validated_profile_required,
    a.is_two_fa_required
FROM nf_projects_with_ar p
JOIN synapse_data_warehouse.synapse.accessrequirement_latest a
    ON p.ar_id = a.id
ORDER BY p.entity_id, a.id;
