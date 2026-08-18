# -*- coding: utf-8 -*-
import re
SAMPLE_EDITORIAL_HTML = """\
<div class="col-sm-12">
<div class="editorial-section">
<ul>
<li class="hidden lang-other">
<a href="/jump?url=https%3A%2F%2Fblog.hamayanhamayan.com%2Fentry%2F2019%2F08%2F19%2F024027" target="_blank" rel="noopener">ユーザ解説</a> <span class="grey">by</span> <a href="/users/hamayanhamayan"><span>hamayanhamayan</span></a>
</li>
<li>
<span class="label label-default">公式</span>
<a href="https://img.atcoder.jp/abc138/editorial.pdf" target="_blank" rel="noopener">解説</a> <span class="grey">by</span> <a href="/users/admin"><span>admin</span></a>
</li>
</ul>
<p class="no-editorial-msg hidden">解説がまだありません。</p>
</div>
</div>
"""
for m in re.finditer(r"<div class=\"editorial-section\">(.*?)</div>", SAMPLE_EDITORIAL_HTML, re.DOTALL):
    block = m.group(1)
    lis = re.findall(r"<li[^>]*>(.*?)</li>", block, re.DOTALL)
    print("num lis:", len(lis))
    for i, li in enumerate(lis):
        print(f"--- li {i} len {len(li)} ---")
        print(repr(li))
        print("has by:", "by</span>" in li)
