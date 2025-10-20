-- Supabase RLS (Row Level Security) policies for voice profiles

-- Enable RLS on voice_profiles table
alter table voice_profiles enable row level security;

-- Users can only view their own voice profiles
create policy "Users can view their own voice profiles"
on voice_profiles for select
to authenticated
using (user_id = auth.uid()::text);

-- Users can only insert their own voice profiles
create policy "Users can insert their own voice profiles"
on voice_profiles for insert
to authenticated
with check (user_id = auth.uid()::text);

-- Users can only delete their own voice profiles
create policy "Users can delete their own voice profiles"
on voice_profiles for delete
to authenticated
using (user_id = auth.uid()::text);

-- Storage policies for voice embeddings
-- Users can only upload to their own folder
create policy "Users can upload voice embeddings"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'voices' 
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Users can only read their own voice embeddings
create policy "Users can read their own voice embeddings"
on storage.objects for select
to authenticated
using (
  bucket_id = 'voices' 
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Users can only delete their own voice embeddings
create policy "Users can delete their own voice embeddings"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'voices' 
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Set storage bucket limits
-- Note: This would be configured in the Supabase dashboard
-- Bucket: voices
-- Max size per object: 6MB
-- Max objects per user: 10 (adjust based on tier)