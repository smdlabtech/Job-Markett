if __name__ == "__main__":
    from extract import extract_all_jobs
    from transform import transform_jobs
    from load import load_jobs_to_db

    extract_all_jobs()
    transform_jobs()
    load_jobs_to_db()