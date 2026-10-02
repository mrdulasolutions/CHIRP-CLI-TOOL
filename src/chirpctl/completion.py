"""Shell completion helpers."""

from __future__ import annotations

import sys

from chirpctl import profiles
from chirpctl.groups import list_groups


def zsh_completion() -> str:
    profiles_list = " ".join(p.name for p in profiles.list_profiles())
    groups_list = " ".join(list_groups().keys())
    targets = f"{profiles_list} {groups_list} all".strip()
    return f"""#compdef chirpctl
_chirpctl() {{
  local -a commands
  commands=(
    'ports:List serial ports'
    'status:Profile and port dashboard'
    'doctor:Health checks'
    'setup:First-run setup'
    'detect:Try to identify radio on port'
    'program:Backup import upload verify'
    'restore:Restore from backup image'
    'backups:List backup images'
    'read:Download from radio'
    'write:Upload to radio'
    'verify:Upload and read back'
    'diff:Compare channel plans'
    'copy:Copy channels'
    'wizard:Interactive helper'
    'profile:Manage profiles'
    'group:Profile groups'
    'fleet:All profiles'
    'channels:Memory operations'
    'snapshots:Named plans'
    'settings:Radio settings'
    'csv:CSV tools'
    'skill:Agent skill install'
    'completion:Shell completion'
  )
  if (( CURRENT == 2 )); then
    _describe 'command' commands
  elif (( CURRENT == 3 )) && [[ $words[2] == program ]]; then
    _describe 'target' ({targets})
  fi
}}
_chirpctl "$@"
"""

def emit_completion(shell: str) -> None:
    if shell == "zsh":
        sys.stdout.write(zsh_completion())
    else:
        raise ValueError(f"Unsupported shell: {shell}")
