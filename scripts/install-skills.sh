#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/install-skills.sh codex [--repo DIR] [--force]
  scripts/install-skills.sh claude [--repo DIR] [--force]

Modes:
  codex   Install Mindthus as a namespaced skills pack at ${CODEX_HOME:-~/.codex}/skills/mindthus.
  claude  Link each skill into ~/.claude/skills without a namespace prefix.

Options:
  --repo DIR  Repository checkout to install from. Defaults to this script's parent.
  --force     Replace an existing symlink or directory at the target path.
USAGE
}

repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${script_dir}/.." && pwd
}

link_path() {
  local source="$1"
  local target="$2"
  local force="$3"

  mkdir -p "$(dirname "${target}")"
  if [[ -e "${target}" || -L "${target}" ]]; then
    if [[ "${force}" != "1" ]]; then
      echo "target already exists: ${target}" >&2
      echo "rerun with --force to replace it" >&2
      return 1
    fi
    rm -rf "${target}"
  fi
  ln -s "${source}" "${target}"
}

mode="${1:-}"
if [[ -z "${mode}" || "${mode}" == "-h" || "${mode}" == "--help" ]]; then
  usage
  exit 0
fi
shift

repo="$(repo_root)"
force="0"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="$2"
      shift 2
      ;;
    --force)
      force="1"
      shift
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

repo="$(cd "${repo}" && pwd)"
skills_dir="${repo}/skills"
if [[ ! -d "${skills_dir}" ]]; then
  echo "skills directory not found: ${skills_dir}" >&2
  exit 1
fi

case "${mode}" in
  codex)
    codex_home="${CODEX_HOME:-${HOME}/.codex}"
    target="${codex_home}/skills/mindthus"
    link_path "${skills_dir}" "${target}" "${force}"
    echo "installed Mindthus skills pack: ${target} -> ${skills_dir}"
    ;;
  claude)
    for skill in "${skills_dir}"/*; do
      [[ -d "${skill}" ]] || continue
      [[ "$(basename "${skill}")" == "_runtime" ]] && continue
      link_path "${skill}" "${HOME}/.claude/skills/$(basename "${skill}")" "${force}"
    done
    echo "installed Mindthus skills into ${HOME}/.claude/skills"
    ;;
  *)
    echo "unknown mode: ${mode}" >&2
    usage >&2
    exit 1
    ;;
esac
