-- Create voice_profiles table
create table voice_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  label text not null,
  path text not null,
  created_at timestamptz default now()
);

-- Create index for faster queries
create index on voice_profiles (user_id);

-- Set up storage bucket for voice embeddings
insert into storage.buckets (id, name, public)
values ('voices', 'voices', false);

-- Set up access policies
create policy "Users can upload voice profiles"
on storage.objects for insert
to authenticated
with check (bucket_id = 'voices');

create policy "Users can read their own voice profiles"
on storage.objects for select
to authenticated
using (bucket_id = 'voices' and owner = auth.uid());

create policy "Users can delete their own voice profiles"
on storage.objects for delete
to authenticated
using (bucket_id = 'voices' and owner = auth.uid());