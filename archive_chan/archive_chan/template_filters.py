import copy
import re
from jinja2 import Markup, escape, evalcontextfilter
from . import bl

def board_url_query(parameters, name=None, value=None):
    parameters = copy.copy(parameters)
    parameters['sort'] = parameters['sort_with_operator']

    if name:
        parameters[name] = value

    query =  '?sort=%s&saved=%s&last_reply=%s&tagged=%s' % (
        parameters['sort'],
        parameters['saved'],
        parameters['last_reply'],
        parameters['tagged'],
    )

    if parameters['tag'] is not None:
        query = '%s&tag=%s' % (
            query,
            urllib.parse.quote('+'.join(parameters['tag']))
        )

    return query


@evalcontextfilter
def format_post(eval_ctx, text):
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


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


bl.add_app_template_filter(board_url_query, 'board_url_query')
bl.add_app_template_filter(format_post, 'formatpost')
bl.add_app_template_filter(nl2br, 'nl2br')
