-- PicksBuy upgrade 3: a size can have its own price (sizes[].p). Run once in Supabase > SQL editor.
create or replace function place_order(items jsonb, customer jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare it jsonb; p products; v text; n int; have int; got jsonb := '[]'; miss jsonb := '[]';
        total numeric := 0; ono text; newsizes jsonb; ship numeric; g text; hold numeric; sp numeric; unit numeric;
begin
  if jsonb_typeof(items) <> 'array' or jsonb_array_length(items) = 0 or jsonb_array_length(items) > 30 then
    raise exception 'bad items'; end if;
  for it in select value from jsonb_array_elements(items) loop
    n := greatest(1, least(coalesce((it->>'n')::int, 1), 20));
    v := coalesce(it->>'v', '');
    select * into p from products where id = it->>'id' and not hidden for update;
    if not found then miss := miss || jsonb_build_object('id', it->>'id', 'v', v); continue; end if;
    if jsonb_array_length(p.sizes) > 0 then
      have := null; sp := null;
      select coalesce((e->>'q')::int, 0), nullif(e->>'p','')::numeric into have, sp
        from jsonb_array_elements(p.sizes) e where e->>'s' = v limit 1;
      have := coalesce(have, 0);
      if v = '' or have < n then miss := miss || jsonb_build_object('id', p.id, 'v', v, 'name', p.name, 'have', have); continue; end if;
      select jsonb_agg(case when t.e->>'s' = v then jsonb_set(t.e, '{q}', to_jsonb(coalesce((t.e->>'q')::int,0) - n)) else t.e end order by t.o)
        into newsizes from jsonb_array_elements(p.sizes) with ordinality as t(e, o);
      update products set sizes = newsizes, updated_at = now() where id = p.id;
      unit := case when sp > 0 then sp else p.price end;
    else
      have := coalesce(p.qty, 0);
      if have < n then miss := miss || jsonb_build_object('id', p.id, 'v', v, 'name', p.name, 'have', have); continue; end if;
      update products set qty = qty - n, updated_at = now() where id = p.id;
      unit := p.price;
    end if;
    got := got || jsonb_build_object('id', p.id, 'name', p.name, 'brand', p.brand, 'v', v, 'price', unit, 'n', n);
    total := total + unit * n;
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

create or replace function pb_version() returns int language sql stable as $$ select 3 $$;
grant execute on function pb_version() to anon, authenticated;
