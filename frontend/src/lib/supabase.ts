import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lrmvoldeyetuzuwuazdm.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxybXZvbGRleWV0dXp1d3VhemRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA3NzAyMjQsImV4cCI6MjA3NjM0NjIyNH0.qjldv8fm1VTUcC-fzIoWPeHBHZ1LvLg8_xVl_QVpy1s';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});
