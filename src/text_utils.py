import html
import re


def strip_html(raw):
    # Some sources (e.g. Greenhouse's content=true) double-encode: entities like
    # &lt;div&gt; wrap what is really HTML markup, so unescape before stripping tags,
    # then unescape again for entities that were inside the visible text itself.
    unescaped = html.unescape(raw)
    no_tags = re.sub(r"<[^>]+>", " ", unescaped)
    return html.unescape(re.sub(r"\s+", " ", no_tags)).strip()
