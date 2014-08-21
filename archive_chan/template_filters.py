"""
    Template filters can be used to modify variables while displaying them
    in the templates. The context processors defined here are attached
    to a blueprint which has to be registered on an application later.
"""


import re
from jinja2 import Markup, escape, evalcontextfilter
from flask import Blueprint


bl = Blueprint('template_filters', __name__)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
_post_link_re = re.compile(r'(?P<text>&gt;&gt;(?P<post_id>[0-9]+))')
_quote_re = re.compile(r'^(&gt;.*)$', flags=re.MULTILINE)
_code_re = re.compile(r'\[code\](.*?)\[\/code\]', flags=re.MULTILINE|re.DOTALL)


@bl.app_template_filter()
@evalcontextfilter
def formatpost(eval_ctx, text):
    """Formats a comment before displaying it in the template."""
    text = str(escape(text))

    # Transform a >>quote into a link.
    text = re.sub(
        _post_link_re,
        r'<a class="post-link" post_id="\g<post_id>">\g<text></a>',
        text
    )

    # Wrap >le meme arrows in <span>.
    text = re.sub(
        _quote_re,
        r'<span class="greentext">\1</span>',
        text
    )

    # Replace [code]i++;[/code] with <pre><code><code></pre>.
    text = re.sub(
        _code_re,
        r'<pre><code>\1</code></pre>',
        text
    )

    if eval_ctx.autoescape:
        text = Markup(text)
    return text


@bl.app_template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """Replaces new line characters with <br> tags."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@bl.app_template_filter()
def datetimeformat(datetime, timeago=True):
    """Converts datetime to <time> tag or readable string."""
    readable = datetime.strftime('%Y-%m-%d %H:%M:%S %z')
    if not timeago:
        return readable
    iso_format = datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
    return Markup('<time class="timeago" datetime="%s">%s</time>' % (
        iso_format,
        readable
    ))
