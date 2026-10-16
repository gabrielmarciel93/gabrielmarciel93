"""Gera um cartão SVG usando apenas dados públicos da API REST do GitHub."""

import argparse
import json
from html import escape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def fetch_json(path):
    request = Request(
        f"https://api.github.com/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-profile-readme",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # Sem token: os dados são públicos e não exigem acesso a outros repositórios.
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_stats(username):
    username = quote(username, safe="")
    profile = fetch_json(f"users/{username}")
    repositories = []
    page = 1
    while True:
        batch = fetch_json(
            f"users/{username}/repos?type=owner&per_page=100&page={page}"
        )
        repositories.extend(repo for repo in batch if not repo["private"])
        if len(batch) < 100:
            break
        page += 1

    return [
        ("Repositórios públicos", len(repositories)),
        ("Estrelas recebidas", sum(repo["stargazers_count"] for repo in repositories)),
        ("Forks recebidos", sum(repo["forks_count"] for repo in repositories)),
        ("Seguidores", profile["followers"]),
    ]


def render_card(username, stats):
    rows = []
    for index, (label, value) in enumerate(stats):
        y = 65 + index * 25
        number = f"{value:,}".replace(",", ".")
        rows.append(
            f'<text x="25" y="{y}" class="label">{escape(label)}</text>'
            f'<text x="420" y="{y}" class="value">{number}</text>'
        )

    description = escape(
        f"Estatísticas públicas de {username}: "
        + "; ".join(f"{label}: {value}" for label, value in stats)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="445" height="165"
  viewBox="0 0 445 165" role="img" aria-labelledby="title description">
  <title id="title">GitHub em números</title>
  <desc id="description">{description}</desc>
  <style>
    text {{ font-family: 'Segoe UI', Ubuntu, sans-serif; }}
    .heading {{ font-size: 18px; font-weight: 600; fill: #ff6e96; }}
    .label {{ font-size: 14px; fill: #f8f8f2; }}
    .value {{ font-size: 14px; font-weight: 600; fill: #79dafa; text-anchor: end; }}
  </style>
  <rect width="445" height="165" rx="5" fill="#282a36"/>
  <text x="25" y="35" class="heading">GitHub em números</text>
  {"\n  ".join(rows)}
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--output", default="dist/stats.svg")
    args = parser.parse_args()

    stats = fetch_stats(args.username)
    svg = render_card(args.username, stats)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"Cartão gerado: {output}")


if __name__ == "__main__":
    main()
