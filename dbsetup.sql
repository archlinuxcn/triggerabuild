create schema if not exists triggerabuild;
set search_path to triggerabuild;

create table to_build (
  id serial primary key,
  ts timestamp with time zone not null default current_timestamp,
  pkgbase text not null
);
