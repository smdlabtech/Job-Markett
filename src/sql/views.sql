CREATE OR REPLACE VIEW vw_job_offers_summary AS
SELECT
    j.status,
    j.job_id,
    j.external_id,
    s.name AS source,
    c.name AS company,
    l.location,
    l.code_postal,
    l.country,
    j.salary_min,
    j.salary_max,
    j.created_at
FROM job_offers j
LEFT JOIN sources s ON j.source_id = s.source_id
LEFT JOIN companies c ON j.company_id = c.company_id
LEFT JOIN locations l ON j.location_id = l.location_id;


CREATE OR REPLACE VIEW vw_offers_by_source AS
SELECT
    s.name AS source,
    COUNT(*) AS offers_count
FROM job_offers j
JOIN sources s ON j.source_id = s.source_id
GROUP BY s.name
ORDER BY offers_count DESC;


CREATE OR REPLACE VIEW vw_offers_by_day AS
SELECT
    date_trunc('day', j.created_at) AS day,
    COUNT(*) AS offers_count
FROM job_offers j
GROUP BY day
ORDER BY day;


CREATE OR REPLACE VIEW vw_job_offers_desc_country AS
SELECT
    j.job_id,
    j.external_id,
    l.country,
    spec.description
FROM job_offers j
LEFT JOIN locations l ON j.location_id = l.location_id
LEFT JOIN (
    SELECT job_id, description FROM france_travail_offers
    UNION ALL
    SELECT job_id, description FROM france_travail_offers
    UNION ALL
    SELECT job_id, description FROM jsearch_offers
) spec ON j.job_id = spec.job_id;
