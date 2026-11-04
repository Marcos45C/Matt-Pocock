#!/bin/sh
set -eu

# Crea un worktree por ticket con el .venv del repo enlazado, y lo elimina.
#
# Uso:
#   scripts/worktree.sh <nombre> [ref-base]
#   scripts/worktree.sh --remove <nombre>
#
# Crea la rama ticket/<nombre> en <ref-base> (por defecto HEAD) y el worktree
# en <repo>-worktrees/<nombre>. Variables opcionales:
#   BRANCH         nombre de rama a crear en lugar de ticket/<nombre>
#   WORKTREE_ROOT  carpeta destino en lugar de <repo>-worktrees
#
# El worktree comparte el .venv del repo: `uv run --locked` no reinstala nada.

usage() {
    echo "Uso: scripts/worktree.sh <nombre> [ref-base]" >&2
    echo "     scripts/worktree.sh --remove <nombre>" >&2
    exit 2
}

[ $# -ge 1 ] || usage

repo=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
root=${WORKTREE_ROOT:-"$(dirname "$repo")/$(basename "$repo")-worktrees"}

if [ "$1" = "--remove" ]; then
    [ $# -eq 2 ] || usage
    name=$2
    path=$root/$name
    branch=${BRANCH:-ticket/$name}
    git worktree remove --force "$path"
    git branch -d "$branch"
    rmdir "$root" 2>/dev/null || true
    echo "Eliminado: $path (rama $branch)"
    exit 0
fi

[ $# -le 2 ] || usage
name=$1
base=${2:-HEAD}
branch=${BRANCH:-ticket/$name}
path=$root/$name

if [ -e "$path" ]; then
    echo "Ya existe el worktree $path" >&2
    exit 1
fi
if git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "Ya existe la rama $branch" >&2
    exit 1
fi

mkdir -p "$root"
git worktree add -b "$branch" "$path" "$base"

if [ -d "$repo/.venv" ]; then
    ln -s "$repo/.venv" "$path/.venv"
else
    echo "Aviso: falta $repo/.venv; ejecutá 'uv sync --locked' antes de correr pruebas." >&2
fi

echo "Worktree: $path"
echo "Rama:     $branch (base $base)"
echo "Pruebas:  cd \"$path\" && uv run --locked python manage.py test --noinput"
