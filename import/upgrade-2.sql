-- ===================== PicksBuy update 2 =====================
-- Safe to run more than once.

alter table orders add column if not exists phone text;
alter table orders add column if not exists gov text;
alter table orders add column if not exists shipping numeric;
alter table orders add column if not exists updated_at timestamptz not null default now();
alter table countries add column if not exists info text default '';

create table if not exists requests (
  id bigserial primary key, created_at timestamptz not null default now(),
  name text, phone text, country text, link text, note text, status text not null default 'new');
alter table requests enable row level security;
drop policy if exists r on requests; create policy r on requests for select using (is_admin());
drop policy if exists w on requests; create policy w on requests for update using (is_admin()) with check (is_admin());
drop policy if exists d on requests; create policy d on requests for delete using (is_admin());
drop policy if exists d on orders;   create policy d on orders for delete using (is_admin());

-- put an order's quantities back on the shelf
create or replace function _restock(items jsonb) returns void
language plpgsql security definer set search_path = public as $$
declare it jsonb; p products; newsizes jsonb;
begin
  for it in select value from jsonb_array_elements(items) loop
    select * into p from products where id = it->>'id' for update;
    if not found then continue; end if;
    if coalesce(it->>'v','') <> '' and jsonb_array_length(p.sizes) > 0 then
      select jsonb_agg(case when t.e->>'s' = it->>'v' then jsonb_set(t.e, '{q}', to_jsonb(coalesce((t.e->>'q')::int,0) + (it->>'n')::int)) else t.e end order by t.o)
        into newsizes from jsonb_array_elements(p.sizes) with ordinality as t(e, o);
      update products set sizes = newsizes, updated_at = now() where id = p.id;
    else
      update products set qty = coalesce(qty,0) + (it->>'n')::int, updated_at = now() where id = p.id;
    end if;
  end loop;
end $$;
revoke execute on function _restock(jsonb) from public, anon, authenticated;

-- checkout v2: phone, governorate and shipping fee from the shop settings
create or replace function place_order(items jsonb, customer jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare it jsonb; p products; v text; n int; have int; got jsonb := '[]'; miss jsonb := '[]';
        total numeric := 0; ono text; newsizes jsonb; ship numeric; g text; hold numeric;
begin
  if jsonb_typeof(items) <> 'array' or jsonb_array_length(items) = 0 or jsonb_array_length(items) > 30 then
    raise exception 'bad items'; end if;
  for it in select value from jsonb_array_elements(items) loop
    n := greatest(1, least(coalesce((it->>'n')::int, 1), 20));
    v := coalesce(it->>'v', '');
    select * into p from products where id = it->>'id' and not hidden for update;
    if not found then miss := miss || jsonb_build_object('id', it->>'id', 'v', v); continue; end if;
    if jsonb_array_length(p.sizes) > 0 then
      select coalesce((e->>'q')::int, 0) into have from jsonb_array_elements(p.sizes) e where e->>'s' = v limit 1;
      have := coalesce(have, 0);
      if v = '' or have < n then miss := miss || jsonb_build_object('id', p.id, 'v', v, 'name', p.name, 'have', have); continue; end if;
      select jsonb_agg(case when t.e->>'s' = v then jsonb_set(t.e, '{q}', to_jsonb(coalesce((t.e->>'q')::int,0) - n)) else t.e end order by t.o)
        into newsizes from jsonb_array_elements(p.sizes) with ordinality as t(e, o);
      update products set sizes = newsizes, updated_at = now() where id = p.id;
    else
      have := coalesce(p.qty, 0);
      if have < n then miss := miss || jsonb_build_object('id', p.id, 'v', v, 'name', p.name, 'have', have); continue; end if;
      update products set qty = qty - n, updated_at = now() where id = p.id;
    end if;
    got := got || jsonb_build_object('id', p.id, 'name', p.name, 'brand', p.brand, 'v', v, 'price', p.price, 'n', n);
    total := total + p.price * n;
  end loop;
  if jsonb_array_length(got) = 0 then return jsonb_build_object('ok', false, 'missing', miss); end if;
  g := left(coalesce(customer->>'gov', ''), 60);
  select nullif(e->>'fee','')::numeric into ship
    from settings s, jsonb_array_elements(coalesce(s.data->'shipping','[]')) e where s.id = 1 and e->>'name' = g limit 1;
  select coalesce((data->>'holdHours')::numeric, 6) into hold from settings where id = 1;
  ono := 'PB-' || upper(substr(md5(random()::text || clock_timestamp()::text), 1, 5));
  insert into orders (order_no, items, total, customer, phone, gov, shipping)
    values (ono, got, total, customer, left(coalesce(customer->>'phone',''), 30), g, ship);
  return jsonb_build_object('ok', true, 'order_no', ono, 'items', got, 'total', total, 'shipping', ship,
                            'hold', coalesce(hold, 6), 'missing', miss);
end $$;
grant execute on function place_order(jsonb, jsonb) to anon, authenticated;

-- orders nobody confirmed in time go back on sale (runs whenever someone opens the shop)
create or replace function release_expired() returns int
language plpgsql security definer set search_path = public as $$
declare hold numeric; o orders; cnt int := 0;
begin
  select coalesce((data->>'holdHours')::numeric, 6) into hold from settings where id = 1;
  if hold is null or hold <= 0 then return 0; end if;
  for o in select * from orders where status = 'new' and created_at < now() - make_interval(secs => hold * 3600)
           order by id for update skip locked loop
    perform _restock(o.items);
    update orders set status = 'expired', updated_at = now() where id = o.id;
    cnt := cnt + 1;
  end loop;
  return cnt;
end $$;
grant execute on function release_expired() to anon, authenticated;

-- admin: move an order along (new -> confirmed -> shipped -> delivered) or cancel it
create or replace function set_order_status(oid bigint, st text) returns text
language plpgsql security definer set search_path = public as $$
declare o orders;
begin
  if not is_admin() then raise exception 'not allowed'; end if;
  if st not in ('new','confirmed','shipped','delivered','cancelled') then raise exception 'bad status'; end if;
  select * into o from orders where id = oid for update;
  if not found then raise exception 'no order'; end if;
  if o.status in ('cancelled','expired') then return o.status; end if;
  if st = 'cancelled' then perform _restock(o.items); end if;
  update orders set status = st, updated_at = now() where id = oid;
  return st;
end $$;
grant execute on function set_order_status(bigint, text) to authenticated;

-- old cancel button keeps working
create or replace function cancel_order(oid bigint) returns void
language plpgsql security definer set search_path = public as $$
begin perform set_order_status(oid, 'cancelled'); end $$;
grant execute on function cancel_order(bigint) to authenticated;

-- customers asking for a product from abroad
create or replace function submit_request(name text, phone text, country text, link text, note text) returns bigint
language plpgsql security definer set search_path = public as $$
declare rid bigint;
begin
  if coalesce(trim(note),'') = '' and coalesce(trim(link),'') = '' then raise exception 'empty'; end if;
  if (select count(*) from requests where created_at > now() - interval '1 hour') > 60 then raise exception 'busy'; end if;
  insert into requests (name, phone, country, link, note)
    values (left(name,80), left(phone,30), left(country,40), left(link,500), left(note,1000)) returning id into rid;
  return rid;
end $$;
grant execute on function submit_request(text, text, text, text, text) to anon, authenticated;

-- version marker the website checks
create or replace function pb_version() returns int language sql stable as $$ select 2 $$;
grant execute on function pb_version() to anon, authenticated;
