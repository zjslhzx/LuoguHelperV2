import urllib.request

for url in [
    "https://atcoder.jp/contests/abc001/tasks/abc001_1",
    "https://atcoder.jp/contests/abc001/tasks/abc001_a",
    "https://atcoder.jp/contests/abc001/tasks/abc001_1/editorial",
]:
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=15,
        )
        body = r.read().decode("utf-8", "ignore")
        print(url, "->", r.status, "len", len(body))
    except urllib.error.HTTPError as e:
        print(url, "->", e.code)
    except Exception as e:
        print(url, "->", "ERR", e)
