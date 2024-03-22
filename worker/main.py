#!/usr/bin/python3

import sys
import select
import logging
import os
import fcntl
import subprocess

import psycopg2

from . import config

logger = logging.getLogger(__name__)

def lilac_run(pkgs):
  if not pkgs:
    return

  logger.info('build packages: %r', pkgs)
  # cmd = ['flock', config.LILAC_LOCK, 'sleep', str(len(pkgs) * 10)]
  cmd = [config.LILAC_BIN] + list(pkgs)
  subprocess.check_call(cmd, stdin = subprocess.DEVNULL)
  logger.info('build done.')

def wait_lilac():
  lock = os.open(config.LILAC_LOCK, os.O_WRONLY | os.O_CREAT, 0o600)
  try:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    return False
  except BlockingIOError:
    logger.info('waiting lilac...')
    fcntl.flock(lock, fcntl.LOCK_EX)
    return True
  finally:
    os.close(lock)

def once(conn):
  with conn:
    cursor = conn.cursor()
    cursor.execute('delete from to_build returning pkgbase')
    pkgs = {x[0] for x in cursor}

  if pkgs:
    lilac_run(pkgs)

  return bool(pkgs)

def run(conn):
  while True:
    wait_lilac()
    if not once(conn):
      break

def main():
  conn = psycopg2.connect(config.DB_URL)
  with conn:
    cursor = conn.cursor()
    cursor.execute("set search_path to 'triggerabuild'")

  run(conn)

  with conn:
    cursor = conn.cursor()
    cursor.execute('listen triggerabuild')

  poll = select.poll()
  poll.register(conn, select.POLLIN)

  while True:
    poll.poll()
    conn.poll()

    run(conn)

if __name__ == '__main__':
  from nicelogger import enable_pretty_logging
  enable_pretty_logging(logging.INFO)

  try:
    main()
  except KeyboardInterrupt:
    sys.exit(130)

