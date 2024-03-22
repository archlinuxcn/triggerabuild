import asyncio
import os
import fcntl

async def get_lilac_state(lock, repo):
  lock = os.open(lock, os.O_WRONLY | os.O_CREAT, 0o600)
  try:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
    return 'running'
  finally:
    os.close(lock)

  branch = await get_git_branch(repo)
  if branch != 'master':
    return 'conflict'

  return 'sleeping'

async def get_queued_packages(db):
  async with db.acquire() as conn, conn.transaction():
    rs = await conn.fetch('select pkgbase from to_build')
    ret = list(set(r[0] for r in rs))
    ret.sort()
    return ret

async def get_git_branch(d):
  p = await asyncio.create_subprocess_exec(
    'git', 'branch', '--no-color',
    stdout = asyncio.subprocess.PIPE,
    cwd = d,
  )
  out, _err = await p.communicate()
  for line in out.decode().splitlines():
    if line.startswith('* '):
      return line.split(None, 1)[-1]

  return '(unknown branch)'

async def submit_build(db, pkgs):
  async with db.acquire() as conn, conn.transaction():
    await conn.executemany(
      'insert into to_build (pkgbase) values ($1)',
      [(pkg,) for pkg in pkgs],
    )
    await conn.execute('notify triggerabuild')
