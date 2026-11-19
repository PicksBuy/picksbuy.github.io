-- PicksBuy: notify the shop owner when a new order comes in. Run once in Supabase > SQL editor.
alter table public.push_subs add column if not exists admin boolean not null default false;
alter table public.push_cfg add column if not exists last_order bigint not null default 0;
update public.push_cfg set last_order = (select coalesce(max(id),0) from public.orders);

create or replace function public.push_admin_add(p_endpoint text) returns boolean
language plpgsql security definer set search_path=public as $$
begin
  if not coalesce(public.is_admin(),false) then raise exception 'not allowed'; end if;
  update push_subs set admin = true where endpoint = p_endpoint;
  return found;
end $$;

create or replace function public.push_new_orders(p_key text) returns json
language plpgsql security definer set search_path=public as $$
declare v_last bigint; v_top bigint; v_orders json;
begin
  select last_order into v_last from push_cfg where k = p_key;
  if not found then raise exception 'not allowed'; end if;
  select coalesce(max(id),0) into v_top from orders;
  if v_top <= v_last then return json_build_object('orders','[]'::json); end if;
  select coalesce(json_agg(json_build_object('no',order_no,'total',total,'ship',shipping,'name',customer->>'name','gov',gov,
           'n',(select coalesce(sum((i->>'n')::int),0) from jsonb_array_elements(items) i)) order by id),'[]'::json)
    into v_orders from orders where id > v_last and id <= v_top;
  update push_cfg set last_order = v_top where k = p_key;
  return json_build_object('orders',v_orders,'vapid',(select vapid from push_cfg where id=1),
    'subs',(select coalesce(json_agg(json_build_object('endpoint',endpoint,'p256dh',p256dh,'auth',auth)),'[]'::json) from push_subs where admin));
end $$;

grant execute on function public.push_admin_add(text), public.push_new_orders(text) to anon, authenticated;
