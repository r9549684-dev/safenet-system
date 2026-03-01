SELECT
  u.device_id, u.country, u.is_premium, u.trial_ends_at, u.created_at,
  u.post_trial_connect_count,
  CASE
    WHEN u.is_premium THEN 'premium'
    WHEN u.trial_ends_at > NOW() THEN 'trial_active'
    ELSE 'trial_expired'
  END AS status
FROM users u
WHERE u.device_id = '9af931ec-2496-47cf-9325-a1bea5327f6e';

SELECT
  c.server_id, c.allocated_ip, c.is_active, c.last_used_at, c.created_at
FROM user_connections c
JOIN users u ON c.user_id = u.id
WHERE u.device_id = '9af931ec-2496-47cf-9325-a1bea5327f6e'
ORDER BY c.created_at DESC
LIMIT 5;
