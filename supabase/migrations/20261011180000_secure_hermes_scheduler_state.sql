-- Restrict direct client access to Hermes scheduler state.
-- Scheduler access should be performed only by trusted server-side code using service_role.
ALTER TABLE public.hermes_scheduler_state
  ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.hermes_scheduler_state
  FROM anon, authenticated;
