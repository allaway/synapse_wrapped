"""
SQL queries for collecting user-specific Synapse activity data.
"""

from datetime import datetime


def query_user_files_downloaded(user_id, start_date, end_date):
    """Return count and details of files downloaded by a specific user."""
    return f"""
    SELECT
        COUNT(DISTINCT objectdownload_event.file_handle_id) AS file_count,
        SUM(filelatest.content_size) AS total_size_bytes,
        COUNT(DISTINCT objectdownload_event.project_id) AS project_count
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
    JOIN
        synapse_data_warehouse.synapse.file_latest filelatest
    ON
        filelatest.id = objectdownload_event.file_handle_id
    WHERE
        objectdownload_event.user_id = {user_id}
        AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    """


def query_user_top_projects(user_id, start_date, end_date, limit=5):
    """Return top projects accessed by a specific user."""
    return f"""
    WITH project_access AS (
        SELECT
            objectdownload_event.project_id,
            COUNT(DISTINCT objectdownload_event.file_handle_id) AS file_count,
            SUM(filelatest.content_size) AS total_size_bytes,
            COUNT(DISTINCT DATE(objectdownload_event.record_date)) AS access_days
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        JOIN
            synapse_data_warehouse.synapse.file_latest filelatest
        ON
            filelatest.id = objectdownload_event.file_handle_id
        WHERE
            objectdownload_event.user_id = {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY
            objectdownload_event.project_id
    ),
    project_names AS (
        SELECT
            pa.project_id,
            pa.file_count,
            pa.total_size_bytes,
            pa.access_days,
            COALESCE(
                JSON_EXTRACT_PATH_TEXT(nl.ANNOTATIONS, 'annotations.studyName.value[0]'),
                nl.name,
                CAST(pa.project_id AS VARCHAR)
            ) AS project_name
        FROM
            project_access pa
        LEFT JOIN
            synapse_data_warehouse.synapse.node_latest nl
        ON
            pa.project_id = nl.id AND nl.node_type = 'project'
    )
    SELECT
        project_id,
        project_name,
        file_count,
        total_size_bytes,
        access_days
    FROM
        project_names
    ORDER BY
        file_count DESC, access_days DESC
    LIMIT {limit}
    """


def query_user_all_projects(user_id, start_date, end_date):
    """Return all projects accessed by a user for word cloud."""
    return f"""
    WITH project_access AS (
        SELECT DISTINCT
            objectdownload_event.project_id
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        WHERE
            objectdownload_event.user_id = {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    )
    SELECT
        pa.project_id,
        COALESCE(
            JSON_EXTRACT_PATH_TEXT(nl.ANNOTATIONS, 'annotations.studyName.value[0]'),
            nl.name,
            CAST(pa.project_id AS VARCHAR)
        ) AS project_name
    FROM
        project_access pa
    LEFT JOIN
        synapse_data_warehouse.synapse.node_latest nl
    ON
        pa.project_id = nl.id AND nl.node_type = 'project'
    """


def query_user_active_days(user_id, start_date, end_date):
    """Return number of distinct days a user was active on Synapse."""
    return f"""
    SELECT
        COUNT(DISTINCT DATE(record_date)) AS active_days
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event
    WHERE
        user_id = {user_id}
        AND record_date BETWEEN '{start_date}' AND '{end_date}'
    """


def query_user_creations(user_id, start_date, end_date):
    """Return projects, files, and tables created by a user."""
    return f"""
    SELECT
        node_type,
        COUNT(*) AS creation_count
    FROM
        synapse_data_warehouse.synapse.node_latest
    WHERE
        created_by = {user_id}
        AND created_on BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        node_type
    """


def query_user_collaboration_network(user_id, start_date, end_date):
    """
    Return network data of users who downloaded the same files.
    Returns edges between users based on overlapping file downloads.
    Edge weight is based on number of overlapping files downloaded.
    """
    return f"""
    WITH target_user_files AS (
        SELECT DISTINCT
            objectdownload_event.file_handle_id
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        WHERE
            objectdownload_event.user_id = {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    ),
    other_user_files AS (
        SELECT DISTINCT
            objectdownload_event.user_id,
            objectdownload_event.file_handle_id
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        WHERE
            objectdownload_event.user_id != {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    ),
    overlapping_files AS (
        SELECT
            ouf.user_id,
            COUNT(DISTINCT ouf.file_handle_id) AS overlapping_file_count
        FROM
            other_user_files ouf
        INNER JOIN
            target_user_files tuf
        ON
            ouf.file_handle_id = tuf.file_handle_id
        GROUP BY
            ouf.user_id
    )
    SELECT
        user_id,
        0 AS shared_projects,
        overlapping_file_count AS shared_files,
        overlapping_file_count AS collaboration_score
    FROM
        overlapping_files
    WHERE
        overlapping_file_count > 0
    ORDER BY
        collaboration_score DESC
    """


def query_user_top_collaborators(user_id, start_date, end_date, limit=5):
    """
    Return top collaborators based on overlapping files downloaded.
    Also includes shared projects for context.
    """
    return f"""
    WITH target_user_files AS (
        SELECT DISTINCT
            objectdownload_event.file_handle_id,
            objectdownload_event.project_id
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        WHERE
            objectdownload_event.user_id = {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    ),
    other_user_files AS (
        SELECT DISTINCT
            objectdownload_event.user_id,
            objectdownload_event.file_handle_id,
            objectdownload_event.project_id
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event objectdownload_event
        WHERE
            objectdownload_event.user_id != {user_id}
            AND objectdownload_event.record_date BETWEEN '{start_date}' AND '{end_date}'
    ),
    overlapping_files AS (
        SELECT
            ouf.user_id,
            COUNT(DISTINCT ouf.file_handle_id) AS shared_files,
            COUNT(DISTINCT ouf.project_id) AS shared_projects
        FROM
            other_user_files ouf
        INNER JOIN
            target_user_files tuf
        ON
            ouf.file_handle_id = tuf.file_handle_id
        GROUP BY
            ouf.user_id
    )
    SELECT
        ovf.user_id,
        ovf.shared_projects,
        ovf.shared_files,
        ovf.shared_files AS collaboration_score,
        COALESCE(up.user_name, CAST(ovf.user_id AS VARCHAR)) AS collaborator_name
    FROM
        overlapping_files ovf
    LEFT JOIN
        synapse_data_warehouse.synapse.userprofile_latest up
    ON
        ovf.user_id = up.id
    WHERE
        ovf.shared_files > 0
    ORDER BY
        ovf.shared_files DESC
    LIMIT {limit}
    """


def get_user_id_from_username(username):
    """Get user ID from username/email."""
    return f"""
    SELECT
        id AS user_id,
        user_name,
        email
    FROM
        synapse_data_warehouse.synapse.userprofile_latest
    WHERE
        LOWER(user_name) = LOWER('{username}')
        OR LOWER(email) = LOWER('{username}')
    LIMIT 1
    """


def query_user_activity_by_date(user_id, start_date, end_date):
    """Return daily activity counts for GitHub-style heatmap."""
    return f"""
    SELECT
        DATE(record_date) AS activity_date,
        COUNT(*) AS activity_count
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event
    WHERE
        user_id = {user_id}
        AND record_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE(record_date)
    ORDER BY
        activity_date
    """


def query_user_creations_by_date(user_id, start_date, end_date):
    """Return daily creation counts for heatmap."""
    return f"""
    SELECT
        DATE(created_on) AS creation_date,
        COUNT(*) AS creation_count
    FROM
        synapse_data_warehouse.synapse.node_latest
    WHERE
        created_by = {user_id}
        AND created_on BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE(created_on)
    ORDER BY
        creation_date
    """


def query_user_activity_by_month(user_id, start_date, end_date):
    """Return monthly activity summary."""
    return f"""
    SELECT
        DATE_TRUNC('month', record_date) AS month,
        COUNT(DISTINCT DATE(record_date)) AS active_days,
        COUNT(DISTINCT file_handle_id) AS files_downloaded,
        COUNT(DISTINCT project_id) AS projects_accessed
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event
    WHERE
        user_id = {user_id}
        AND record_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE_TRUNC('month', record_date)
    ORDER BY
        month
    """


def query_user_activity_by_hour(user_id, start_date, end_date, timezone='America/Chicago'):
    """Return download activity breakdown by hour of day in the specified timezone."""
    return f"""
    SELECT
        DATE_PART('hour', CONVERT_TIMEZONE('UTC', '{timezone}', timestamp)) AS hour_of_day,
        COUNT(*) AS download_count,
        COUNT(DISTINCT file_handle_id) AS unique_files
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event
    WHERE
        user_id = {user_id}
        AND record_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE_PART('hour', CONVERT_TIMEZONE('UTC', '{timezone}', timestamp))
    ORDER BY hour_of_day
    """


def query_user_time_patterns(user_id, start_date, end_date, timezone='America/Chicago'):
    """Return time-based activity patterns (night owl, early bird, weekday vs weekend) in the specified timezone."""
    return f"""
    WITH download_times AS (
        SELECT
            CONVERT_TIMEZONE('UTC', '{timezone}', timestamp) AS local_timestamp,
            DATE_PART('hour', CONVERT_TIMEZONE('UTC', '{timezone}', timestamp)) AS hour_of_day,
            DAYOFWEEK(CONVERT_TIMEZONE('UTC', '{timezone}', timestamp)) AS day_of_week
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event
        WHERE
            user_id = {user_id}
            AND record_date BETWEEN '{start_date}' AND '{end_date}'
    )
    SELECT
        COUNT(*) AS total_downloads,
        SUM(CASE WHEN hour_of_day >= 18 OR hour_of_day < 6 THEN 1 ELSE 0 END) AS night_downloads,
        SUM(CASE WHEN hour_of_day >= 5 AND hour_of_day < 9 THEN 1 ELSE 0 END) AS early_downloads,
        SUM(CASE WHEN day_of_week IN (0, 6) THEN 1 ELSE 0 END) AS weekend_downloads,
        SUM(CASE WHEN day_of_week NOT IN (0, 6) THEN 1 ELSE 0 END) AS weekday_downloads
    FROM download_times
    """


def query_user_first_download(user_id, start_date, end_date):
    """Return the first download event of the year."""
    return f"""
    SELECT
        od.record_date AS first_download_date,
        COALESCE(nl.name, CONCAT('syn', od.file_handle_id)) AS file_name,
        COALESCE(
            JSON_EXTRACT_PATH_TEXT(pn.ANNOTATIONS, 'annotations.studyName.value[0]'),
            pn.name,
            CAST(od.project_id AS VARCHAR)
        ) AS project_name
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    LEFT JOIN
        synapse_data_warehouse.synapse.node_latest nl
    ON
        od.file_handle_id = nl.file_handle_id
    LEFT JOIN
        synapse_data_warehouse.synapse.node_latest pn
    ON
        od.project_id = pn.id AND pn.node_type = 'project'
    WHERE
        od.user_id = {user_id}
        AND od.record_date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY
        od.record_date ASC
    LIMIT 1
    """


def query_user_busiest_day(user_id, start_date, end_date):
    """Return the user's busiest download day of the year."""
    return f"""
    SELECT
        DATE(record_date) AS busiest_date,
        COUNT(*) AS download_count,
        COUNT(DISTINCT file_handle_id) AS unique_files,
        COUNT(DISTINCT project_id) AS projects_accessed,
        SUM(fl.content_size) AS total_size_bytes
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    JOIN
        synapse_data_warehouse.synapse.file_latest fl
    ON
        fl.id = od.file_handle_id
    WHERE
        od.user_id = {user_id}
        AND od.record_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE(record_date)
    ORDER BY
        download_count DESC
    LIMIT 1
    """


def query_user_largest_download(user_id, start_date, end_date):
    """Return the largest single file downloaded by the user."""
    return f"""
    SELECT DISTINCT
        od.file_handle_id,
        COALESCE(nl.name, CONCAT('syn', nl.id)) AS file_name,
        fl.content_size,
        od.record_date,
        COALESCE(
            JSON_EXTRACT_PATH_TEXT(pn.ANNOTATIONS, 'annotations.studyName.value[0]'),
            pn.name,
            CAST(od.project_id AS VARCHAR)
        ) AS project_name
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    JOIN
        synapse_data_warehouse.synapse.file_latest fl ON od.file_handle_id = fl.id
    LEFT JOIN
        synapse_data_warehouse.synapse.node_latest nl ON od.file_handle_id = nl.file_handle_id
    LEFT JOIN
        synapse_data_warehouse.synapse.node_latest pn ON od.project_id = pn.id AND pn.node_type = 'project'
    WHERE
        od.user_id = {user_id}
        AND od.record_date BETWEEN '{start_date}' AND '{end_date}'
        AND fl.content_size IS NOT NULL
    ORDER BY fl.content_size DESC
    LIMIT 1
    """


def query_platform_average_file_size(start_date, end_date):
    """Return the platform-wide average file size for downloads in the period."""
    return f"""
    SELECT
        AVG(fl.content_size) AS avg_file_size,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fl.content_size) AS median_file_size
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    JOIN
        synapse_data_warehouse.synapse.file_latest fl ON od.file_handle_id = fl.id
    WHERE
        od.record_date BETWEEN '{start_date}' AND '{end_date}'
        AND fl.content_size IS NOT NULL
        AND fl.content_size > 0
    """


def query_user_average_file_size(user_id, start_date, end_date):
    """Return the user's average file size for downloads."""
    return f"""
    SELECT
        AVG(fl.content_size) AS avg_file_size,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fl.content_size) AS median_file_size
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    JOIN
        synapse_data_warehouse.synapse.file_latest fl ON od.file_handle_id = fl.id
    WHERE
        od.user_id = {user_id}
        AND od.record_date BETWEEN '{start_date}' AND '{end_date}'
        AND fl.content_size IS NOT NULL
        AND fl.content_size > 0
    """


def query_user_monthly_download_size(user_id, start_date, end_date):
    """Return monthly download sizes for cumulative growth chart."""
    return f"""
    SELECT
        DATE_TRUNC('month', od.record_date) AS month,
        SUM(fl.content_size) AS total_size_bytes,
        COUNT(DISTINCT od.file_handle_id) AS file_count
    FROM
        synapse_data_warehouse.synapse_event.objectdownload_event od
    JOIN
        synapse_data_warehouse.synapse.file_latest fl ON od.file_handle_id = fl.id
    WHERE
        od.user_id = {user_id}
        AND od.record_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        DATE_TRUNC('month', od.record_date)
    ORDER BY
        month
    """


def query_platform_download_ranking(user_id, start_date, end_date):
    """Return the user's ranking among all downloaders (for power user badge)."""
    return f"""
    WITH user_totals AS (
        SELECT
            user_id,
            COUNT(DISTINCT file_handle_id) AS total_files
        FROM
            synapse_data_warehouse.synapse_event.objectdownload_event
        WHERE
            record_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY
            user_id
    ),
    ranked_users AS (
        SELECT
            user_id,
            total_files,
            PERCENT_RANK() OVER (ORDER BY total_files DESC) AS percentile_rank
        FROM user_totals
    )
    SELECT
        user_id,
        total_files,
        percentile_rank,
        (SELECT COUNT(*) FROM user_totals) AS total_users
    FROM ranked_users
    WHERE user_id = {user_id}
    """


def query_user_access_requirements(user_id, start_date, end_date):
    """Return access requirement types for files downloaded by user."""
    return f"""
    WITH user_projects AS (
        SELECT DISTINCT project_id
        FROM synapse_data_warehouse.synapse_event.objectdownload_event
        WHERE user_id = {user_id}
        AND record_date BETWEEN '{start_date}' AND '{end_date}'
    ),
    project_ars AS (
        SELECT
            up.project_id,
            ar.value AS ar_id
        FROM user_projects up
        JOIN synapse_data_warehouse.synapse.node_latest nl ON up.project_id = nl.id
        CROSS JOIN LATERAL FLATTEN(input => nl.effective_ars, OUTER => TRUE) ar
        WHERE nl.node_type = 'project'
    )
    SELECT
        COUNT(DISTINCT up.project_id) AS total_projects,
        COUNT(DISTINCT CASE WHEN pa.ar_id IS NOT NULL THEN up.project_id END) AS controlled_projects,
        COUNT(DISTINCT CASE WHEN pa.ar_id IS NULL THEN up.project_id END) AS open_projects
    FROM user_projects up
    LEFT JOIN project_ars pa ON up.project_id = pa.project_id
    """

