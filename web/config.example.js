// Copy to config.js for local testing, or let scripts/write-config.mjs create it at deploy time.
// Only ever the publishable key. Never a secret or service_role key.
window.RB_CONFIG = { supabaseUrl: "https://YOUR-PROJECT.supabase.co", supabaseKey: "sb_publishable_..." };
