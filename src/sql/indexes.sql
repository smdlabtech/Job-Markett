-- Index sur les clés étrangères de job_offers (pour optimiser les jointures)
CREATE INDEX idx_job_offers_source ON job_offers(source_id);
CREATE INDEX idx_job_offers_company ON job_offers(company_id);
CREATE INDEX idx_job_offers_location ON job_offers(location_id);

-- Index sur created_at pour optimiser les tris et recherches par date
CREATE INDEX idx_job_offers_created_at ON job_offers(created_at DESC);

-- Index full-text pour la recherche avancée sur les titres et descriptions

-- Adzuna
CREATE INDEX idx_title_search_adzuna ON adzuna_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_adzuna ON adzuna_offers USING GIN (to_tsvector('french', description));

-- France Travail
CREATE INDEX idx_title_search_france_travail ON france_travail_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_france_travail ON france_travail_offers USING GIN (to_tsvector('french', description));

-- JSearch
CREATE INDEX idx_title_search_jsearch ON jsearch_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_jsearch ON jsearch_offers USING GIN (to_tsvector('french', description));

-- Logs
CREATE INDEX idx_job_id_logs_ ON job_offers_log(job_id)