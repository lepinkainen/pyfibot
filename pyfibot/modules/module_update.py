from __future__ import unicode_literals, print_function, division
import subprocess
import sys

import logging
from git import Repo, GitCommandError
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger("update")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _git_pull(repo_path):
    """Pull from git with retry logic"""
    repo = Repo(repo_path)
    origin = repo.remotes.origin
    return origin.pull()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _install_dependencies(cwd):
    """Install/upgrade dependencies with retry logic"""
    # Use uv if available, otherwise fall back to pip
    try:
        cmd = ["uv", "sync", "--upgrade"]
        log.debug("Executing uv sync --upgrade in %s" % cwd)
    except FileNotFoundError:
        cmd = ["pip", "install", "--upgrade", "-e", "."]
        log.debug("Executing pip install --upgrade in %s" % cwd)

    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.wait()
    out, err = p.communicate()

    if res != 0:
        raise RuntimeError(f"Command failed with exit code {res}: {err.decode()}")

    return out.decode(), err.decode()


def command_update(bot, user, channel, args):
    """Update bot sources from git"""
    if not bot.isAdmin(user):
        return

    pull_ok = False
    pip_ok = False
    cwd = sys.path[0]

    # Git pull with GitPython and retry logic
    try:
        log.debug("Executing git pull in %s" % cwd)
        pull_info = _git_pull(cwd)

        if pull_info:
            pull_ok = True
            bot.say(channel, "Git update OK:")
            for info in pull_info:
                if hasattr(info, "commit"):
                    bot.say(
                        channel,
                        f"Updated to {info.commit.hexsha[:8]}: {info.commit.summary}",
                    )
        else:
            pull_ok = True
            bot.say(channel, "Already up to date")

    except GitCommandError as e:
        bot.say(channel, f"Git pull failed: {e}")
        log.error(f"Git pull failed: {e}")
    except Exception as e:
        bot.say(channel, f"Git operation failed: {e}")
        log.error(f"Git operation failed: {e}")

    # Install/upgrade dependencies
    try:
        out, err = _install_dependencies(cwd)
        bot.say(channel, "Package dependencies updated successfully")
        pip_ok = True

        # Log detailed output for debugging
        if out:
            log.debug(f"Package install output: {out}")
        if err:
            log.debug(f"Package install stderr: {err}")

    except Exception as e:
        bot.say(channel, f"Package update failed: {e}")
        log.error(f"Package update failed: {e}")

    # Rehash after successful update
    if pip_ok and pull_ok:
        bot.command_rehash(user, channel, args)
