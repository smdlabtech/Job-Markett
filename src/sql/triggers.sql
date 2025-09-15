CREATE OR REPLACE FUNCTION log_job_offers_changes()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'insert_job_offers', NEW.created_at);
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        -- 1) Si on désactive l'offre (status passe d'active à inactive) :
        IF OLD.status = 'active' AND NEW.status = 'inactive' THEN
            INSERT INTO job_offers_log (
                job_id, action, created_at, deleted_at
            )
            VALUES (
                OLD.job_id,
                'delete_job_offers',
                OLD.created_at,
                NOW()
            );
        -- 2) Sinon, c'est un update classique :
        ELSE
            INSERT INTO job_offers_log (
                job_id, action, created_at, updated_at
            )
            VALUES (
                OLD.job_id,
                'update_job_offers',
                OLD.created_at,
                NOW()
            );
        END IF;

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_job_offers_changes ON job_offers;
CREATE TRIGGER trg_job_offers_changes
AFTER INSERT OR UPDATE ON job_offers
FOR EACH ROW EXECUTE FUNCTION log_job_offers_changes();
