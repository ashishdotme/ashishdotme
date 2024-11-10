import feedparser
import httpx
import json
import pathlib
import re
import os

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(
        marker, chunk, marker)
    return r.sub(chunk, content)


def replace_chunk_no_space(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->`{}`<!-- {} ends -->".format(
        marker, chunk, marker)
    return r.sub(chunk, content)


def fetch_wiki():
    sql = "select title, url, created_utc from notes order by created_utc desc limit 5"
    return httpx.get(
        "https://notes.ashish.me/notes.json",
        params={"sql": sql, "_shape": "array", },
    ).json()

def fetch_weeknotes():
    response = httpx.get("https://blog.ashish.me/weekly/all.json").json()
    return response

def fetch_movie():
    movie = httpx.get("https://api.ashish.me/movies").json()[0]["title"]
    return movie

def fetch_tv():
    tv = httpx.get("https://api.ashish.me/shows").json()[0]["title"]
    return tv

def fetch_blog_entries():
    entries = feedparser.parse("https://ashish.me/feed.xml")["entries"]
    return [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("00")[0],
        }
        for entry in entries
    ]


if __name__ == "__main__":
    readme = root / "README.md"
    readme_contents = readme.open().read()

    wikis = fetch_wiki()
    wikis_md = "\n".join(
        [
            "- [{title}]({url}) - {created_at}".format(
                title=wiki["title"],
                url=wiki["url"],
                created_at=wiki["created_utc"].split("T")[0],
            )
            for wiki in wikis
        ]
    )
    rewritten = replace_chunk(readme_contents, "wiki", wikis_md)

    movie = fetch_movie()
    rewritten = replace_chunk_no_space(rewritten, "movie", movie, True)

    tv = fetch_tv()
    rewritten = replace_chunk_no_space(rewritten, "tv", tv, True)

    weeknotes = fetch_weeknotes()[:10]
    weeknotes_md = "\n".join(
        [
            "- [{title}]({url}) - {published}".format(
                title=weeknote["title"],
                url="https://ashish.me/weekly/" + weeknote["slug"],
                published=weeknote["date"].split("T")[0]
            )
            for weeknote in reversed(weeknotes)
        ]
    )
    rewritten = replace_chunk(rewritten, "weeknotes", weeknotes_md)

    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join(
        ["- [{title}]({url}) - {published}".format(**entry)
         for entry in entries]
    )
    rewritten = replace_chunk(rewritten, "blog", entries_md)

    readme.open("w").write(rewritten)
