#!/usr/bin/python3

import logging
import os

import aiohttp
from aiohttp import web
from aiohttp_session import setup, get_session, new_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
from yarl import URL
import asyncpg

from . import config
from . import funcs

logger = logging.getLogger(__name__)
KEY_DB = web.AppKey('db', asyncpg.Pool)

async def pkglist(request):
  ret = []
  with os.scandir(config.REPODIR) as it:
    for entry in it:
      if not entry.name.startswith('.') and entry.is_dir():
        ret.append(entry.name)
  ret.sort()
  return web.json_response({'data': ret})

async def info(request):
  session = await get_session(request)
  ret = {
    "username": session.get('username'),
    "lilac": await funcs.get_lilac_state(config.LILAC_LOCK, config.LILAC_REPO),
    "queued": await funcs.get_queued_packages(request.app[KEY_DB]),
  }
  return web.json_response({'data': ret})

async def github_login(request):
  code = request.query.get('code')
  if not code:
    url = URL('https://github.com/login/oauth/authorize') % {
      'client_id': config.CLIENT_ID,
      'redirect_uri': 'http://127.0.0.1:9008/triggerabuild/login',
      'scope': 'read:org',
    }
    raise web.HTTPFound(str(url))

  async with aiohttp.ClientSession() as session:
    url = 'https://github.com/login/oauth/access_token'
    data = {
      'client_id': config.CLIENT_ID,
      'client_secret': config.CLIENT_SECRET,
      'code': code,
    }
    headers = {
      'Accept': 'application/json',
    }
    async with session.post(url, data=data, headers=headers) as res:
      j = await res.json()
      access_token = j['access_token']

    url = 'https://api.github.com/user/orgs'
    headers = {
      'Accept': 'application/vnd.github+json',
      'Authorization': f'Bearer {access_token}',
      'X-GitHub-Api-Version': '2022-11-28',
    }
    async with session.get(url, headers=headers) as res:
      j = await res.json()
      orgs = [o['login'] for o in j]
      if config.TARGET_ORG not in orgs:
        raise web.HTTPForbidden()

    url = 'https://api.github.com/user'
    async with session.get(url, headers=headers) as res:
      j = await res.json()
      username = j['login']
    session = await new_session(request)
    session['username'] = username

  raise web.HTTPFound('/triggerabuild/')

async def submit(request):
  session = await get_session(request)
  username = session.get('username')
  if not username:
    raise web.HTTPForbidden()

  to_build = await request.json()
  logger.info('%s wants to build %s.', username, to_build)
  await funcs.submit_build(request.app[KEY_DB], to_build)
  return web.json_response({})

async def init_db(app):
  app[KEY_DB] = await asyncpg.create_pool(config.DB_URL, setup=conn_init, min_size=0)
  yield
  await app[KEY_DB].close()

async def conn_init(conn):
  await conn.execute("set search_path to 'triggerabuild'")

def setup_app(app):
  app.cleanup_ctx.append(init_db)

  f = fernet.Fernet(config.FERNET_KEY)
  setup(app, EncryptedCookieStorage(
    f, path='/triggerabuild/', max_age=86400 * 30,
    secure=True, samesite='None',
  ))

  app.router.add_get('/triggerabuild/pkglist', pkglist)
  app.router.add_get('/triggerabuild/info', info)
  app.router.add_get('/triggerabuild/login', github_login)
  app.router.add_post('/triggerabuild/submit', submit)

def main():
  import argparse

  from nicelogger import enable_pretty_logging

  parser = argparse.ArgumentParser(
    description = 'trigger a build for lilac',
  )
  parser.add_argument('--port', default=9008, type=int,
                      help='port to listen on')
  parser.add_argument('--ip', default='127.0.0.1',
                      help='address to listen on')
  parser.add_argument('--loglevel', default='info',
                      choices=['debug', 'info', 'warn', 'error'],
                      help='log level')
  args = parser.parse_args()

  enable_pretty_logging(args.loglevel.upper())

  app = web.Application()
  setup_app(app)

  web.run_app(app, host=args.ip, port=args.port)

if __name__ == '__main__':
  main()
