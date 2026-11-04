\pset tuples_only on
\pset format unaligned
select t,
  (xpath('/row/c/text()', query_to_xml(format('select count(*) c from public.%I', t), false, true, '')))[1]::text,
  (xpath('/row/h/text()', query_to_xml(format('select md5(coalesce(string_agg(x::text, ''|'' order by x::text collate "C"), '''')) h from public.%I x', t), false, true, '')))[1]::text
from unnest(array['education','experience','links','profile','projects','settings','skills']) t order by t;
select 'seq', sequencename, last_value from pg_sequences where schemaname='public' order by 2;
select 'constraints', count(*) from pg_constraint c join pg_namespace n on n.oid=c.connamespace where n.nspname='public';
