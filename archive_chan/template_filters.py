"""
    Template filters can be used to modify variables in the template.
"""


import re
from jinja2 import Markup, escape, evalcontextfilter
from . import app


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@app.template_filter()
@evalcontextfilter
def formatpost(eval_ctx, text):
    """This filter formats a post comment before displaying it in the template."""
    text = str(escape(text))

    # >>quote
    text = re.sub(
        r'(?P<text>&gt;&gt;(?P<post_id>[0-9]+))',
        r'<a class="post-link" post_id="\g<post_id>">\g<text></a>',
        text
    )

    # >le meme arrows
    text = re.sub(
        r'^(&gt;.*)$',
        r'<span class="greentext">\1</span>',
        text,
        flags=re.MULTILINE
    )

    # [code]i++;[/code]
    text = re.sub(
        r'\[code\](.*?)\[\/code\]',
        r'<pre><code>\1</code></pre>',
        text,
        flags=re.MULTILINE|re.DOTALL
    )

    if eval_ctx.autoescape:
        text = Markup(text)
    return text


@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@app.template_filter()
def datetimeformat(datetime, timeago=True):
    readable = datetime.strftime('%Y-%m-%d %H:%M:%S %z')
    if not timeago:
        return readable
    iso_format = datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
    return Markup('<time class=timeago datetime="%s">%s</time>' % (
        iso_format,
        readable
    ))
