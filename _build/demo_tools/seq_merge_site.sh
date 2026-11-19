#!/usr/bin/env bash
# Merge site PRs one by one: rebase each branch on the updated main, regenerate project pages,
# push, merge, then move to the next. Stops on any conflict outside generated pages.
set -u
R=karemdm/karemdm.github.io
cd /c/Users/KAREMDAIANEMARCOMINI/Desktop/karemdm.github.io || exit 1
for pair in "$@"; do
  n=${pair%%:*}; b=${pair#*:}
  git checkout -q main && git pull -q --ff-only origin main || exit 1
  git checkout -q "$b" || exit 1
  if ! git rebase -q main >/dev/null 2>&1; then
    while true; do
      U=$(git diff --name-only --diff-filter=U)
      [ -z "$U" ] && break
      if echo "$U" | grep -qvE '^(pt/)?projects/'; then echo "STOP: conflict in $U ($b)"; git rebase --abort; exit 1; fi
      echo "$U" | xargs git checkout --theirs -- && echo "$U" | xargs git add
      GIT_EDITOR=true git rebase --continue >/dev/null 2>&1 && break
    done
  fi
  python -I _build/build_projects.py >/dev/null
  if [ -n "$(git status --porcelain projects pt/projects)" ]; then
    if [ -n "$(git diff --ignore-cr-at-eol --stat projects pt/projects)" ]; then
      git add -A projects pt/projects && git commit -qm "chore: regenerate project pages"
    else
      git checkout -q -- projects pt/projects
    fi
  fi
  git push -q --force-with-lease origin "$b" || exit 1
  sleep 2
  gh pr merge "$n" -R $R --merge --delete-branch >/dev/null 2>&1 || { echo "MERGE FAIL #$n"; exit 1; }
  echo "merged #$n $b"
done
git checkout -q main && git pull -q --ff-only origin main
