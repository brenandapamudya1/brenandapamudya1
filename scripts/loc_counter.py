#!/usr/bin/env python3
"""
Count lines of code authored by the user across owned repositories.

Technique adapted from references.py (Andrew6rant): walk each repo's commit
history via the GraphQL API (100 commits per page), summing additions and
deletions only for commits authored by the user (matched by GraphQL user id).

A per-repo cache file (cache/<sha256(username)>.txt, committed to the repo)
stores `repohash commit_count my_commits additions deletions` per line, so
later runs only re-walk repos whose commit count changed.

No new third-party dependencies: only requests + stdlib.
"""
import hashlib
import os
import time

import requests

API = "https://api.github.com/graphql"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache")
CACHE_DIR = os.path.normpath(CACHE_DIR)


def _post(query, variables, token):
    r = requests.post(
        API,
        json={"query": query, "variables": variables},
        headers={"Authorization": f"bearer {token}"},  # never printed/logged
        timeout=60,
    )
    body = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"status={r.status_code} errors={body.get('errors', body)}")
    return body.get("data") or {}


def get_owner_id(username, token):
    q = "query($login: String!) { user(login: $login) { id } }"
    user = _post(q, {"login": username}, token).get("user") or {}
    if not user.get("id"):
        raise RuntimeError("could not resolve user id")
    return user["id"]


def list_owned_repos(username, token):
    """Return [(nameWithOwner, default-branch commit count)] for OWNER repos."""
    q = """
    query($login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER]) {
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            defaultBranchRef {
                                target {
                                    ... on Commit { history { totalCount } }
                                }
                            }
                        }
                    }
                }
                pageInfo { endCursor hasNextPage }
            }
        }
    }"""
    repos, cursor = [], None
    while True:
        user = _post(q, {"login": username, "cursor": cursor}, token).get("user") or {}
        conn = (user.get("repositories") or {})
        for e in conn.get("edges", []):
            node = e.get("node") or {}
            ref = node.get("defaultBranchRef")
            count = ref["target"]["history"]["totalCount"] if ref else 0
            repos.append((node.get("nameWithOwner", "?"), count))
        if not (conn.get("pageInfo") or {}).get("hasNextPage"):
            break
        cursor = conn["pageInfo"]["endCursor"]
    return repos


def walk_repo(owner, repo, token, owner_id):
    """Walk one repo's history. Returns (my_commits, additions, deletions).

    Only commits whose author.user.id matches owner_id are counted, so
    unlinked-email commits are skipped. Raises on API errors so the caller
    can keep the previous cache entry instead of caching partial data.
    """
    q = """
    query($owner: String!, $repo: String!, $cursor: String) {
        repository(owner: $owner, name: $repo) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            edges {
                                node {
                                    ... on Commit { additions deletions }
                                    author { user { id } }
                                }
                            }
                            pageInfo { endCursor hasNextPage }
                        }
                    }
                }
            }
        }
    }"""
    my_commits = add = dele = 0
    cursor = None
    while True:
        r = requests.post(
            API,
            json={"query": q, "variables": {"owner": owner, "repo": repo, "cursor": cursor}},
            headers={"Authorization": f"bearer {token}"},
            timeout=60,
        )
        body = r.json()
        if r.status_code != 200:
            raise RuntimeError(f"{owner}/{repo}: status={r.status_code} errors={body.get('errors', body)}")
        repo_data = (body.get("data") or {}).get("repository")
        if repo_data is None:
            raise RuntimeError(f"{owner}/{repo}: repository not accessible")
        ref = repo_data.get("defaultBranchRef")
        if ref is None:
            return my_commits, add, dele  # empty repo: normal, not an error
        hist = ref["target"]["history"]
        for e in hist.get("edges", []):
            node = e.get("node") or {}
            author = (node.get("author") or {}).get("user") or {}
            if author.get("id") == owner_id:
                my_commits += 1
                add += node.get("additions") or 0
                dele += node.get("deletions") or 0
        if not (hist.get("pageInfo") or {}).get("hasNextPage"):
            break
        cursor = hist["pageInfo"]["endCursor"]
    return my_commits, add, dele


def _cache_path(username):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, hashlib.sha256(username.encode("utf-8")).hexdigest() + ".txt")


def compute(username, token, progress=None):
    """Return (additions, deletions, net) for the user's own commits.

    Re-walks only repos whose commit count changed since the last run;
    failures keep the previous cache entry so they are retried tomorrow.
    """
    def log(msg):
        if progress:
            progress(msg)

    owner_id = get_owner_id(username, token)
    repos = list_owned_repos(username, token)
    log(f"   loc: {len(repos)} owned repos, owner id resolved")

    path = _cache_path(username)
    cached = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            parts = line.split()
            if len(parts) == 5:
                cached[parts[0]] = parts[1:]

    lines, add_total, del_total = [], 0, 0
    for name, count in repos:
        h = hashlib.sha256(name.encode("utf-8")).hexdigest()
        old = cached.get(h)
        if old and int(old[0]) == count:
            my_c, a, d = int(old[1]), int(old[2]), int(old[3])
            lines.append(f"{h} {count} {my_c} {a} {d}\n")
            log(f"   cached {name}: {my_c} commits +{a}/-{d}")
        else:
            owner, repo = name.split("/", 1)
            try:
                my_c, a, d = walk_repo(owner, repo, token, owner_id)
                lines.append(f"{h} {count} {my_c} {a} {d}\n")
                log(f"   walked {name}: {my_c} commits +{a}/-{d}")
            except Exception as e:
                if old:
                    lines.append(f"{h} {old[0]} {old[1]} {old[2]} {old[3]}\n")
                    my_c, a, d = int(old[1]), int(old[2]), int(old[3])
                else:
                    lines.append(f"{h} 0 0 0 0\n")
                    my_c, a, d = 0, 0, 0
                log(f"   {name}: walk failed ({e}), will retry next run")
            time.sleep(1)
        add_total += a
        del_total += d

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return add_total, del_total, add_total - del_total
