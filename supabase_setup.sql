-- Spin the Bic Bic: the counters, stored in Supabase.
--
-- Run this once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
-- It is safe to run again (it only creates what is missing and refreshes the rules).
--
-- What it sets up:
--   * spin_totals     one row per "namespace" with the worldwide spin total.
--   * sentence_counts one row per sentence (1..106) per namespace with how often it has landed.
--   * "namespace" is 'live' for the real website and 'dev' for testing on your own computer,
--     so testing never changes the real numbers.
--   * Row Level Security is ON. The public (publishable) key may READ both tables and may call
--     record_spin(), which adds exactly 1 to one sentence and to the total. Nothing else:
--     it cannot edit, set, or delete any number directly.

-- ---------- tables ----------
create table if not exists public.spin_totals (
  namespace text primary key check (namespace in ('live', 'dev')),
  total     bigint not null default 0 check (total >= 0),
  baseline  bigint not null default 0 check (baseline >= 0)   -- how many of the spins are stand-ins
);

create table if not exists public.sentence_counts (
  namespace text    not null check (namespace in ('live', 'dev')),
  number    integer not null check (number > 0),
  spins     bigint  not null default 0 check (spins >= 0),
  primary key (namespace, number)
);

-- ---------- starting rows (zeros; the real starting numbers are loaded separately) ----------
-- (One row per sentence, 1 to 106. If you ever add sentences, raise the 106 below and run this file again.)
insert into public.spin_totals (namespace) values ('live'), ('dev')
  on conflict (namespace) do nothing;

insert into public.sentence_counts (namespace, number)
  select ns, n from unnest(array['live', 'dev']) as ns, generate_series(1, 106) as n
  on conflict (namespace, number) do nothing;

-- ---------- who may do what ----------
alter table public.spin_totals     enable row level security;
alter table public.sentence_counts enable row level security;

revoke all on public.spin_totals, public.sentence_counts from anon, authenticated;
grant select on public.spin_totals, public.sentence_counts to anon;

drop policy if exists "public can read totals" on public.spin_totals;
create policy "public can read totals" on public.spin_totals
  for select to anon using (true);

drop policy if exists "public can read counts" on public.sentence_counts;
create policy "public can read counts" on public.sentence_counts
  for select to anon using (true);

-- ---------- the one safe way to count a spin ----------
-- Adds 1 to the total (which also queues spins one at a time, so every player gets a different
-- total back) and 1 to the sentence that landed. Returns the new worldwide total, which is how
-- the page knows when someone has just made spin number 1,000.
create or replace function public.record_spin(p_namespace text, p_number integer)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  new_total bigint;
begin
  update spin_totals set total = total + 1
   where namespace = p_namespace
   returning total into new_total;
  if new_total is null then
    raise exception 'unknown namespace';
  end if;

  update sentence_counts set spins = spins + 1
   where namespace = p_namespace and number = p_number;
  if not found then
    raise exception 'unknown sentence';   -- rolls the whole spin back, nothing is half-counted
  end if;

  return new_total;
end;
$$;

revoke all on function public.record_spin(text, integer) from public, anon, authenticated;
grant execute on function public.record_spin(text, integer) to anon;
