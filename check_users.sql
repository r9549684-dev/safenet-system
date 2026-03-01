SELECT id, device_id, country, trial_ends_at, created_at FROM users WHERE device_id IS NULL OR device_id = '' ORDER BY created_at DESC;
