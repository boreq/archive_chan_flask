import re, cgi, copy, urllib

from django import template

register = template.Library()

@register.filter
def formatpost(text):
    """This filter formats a post comment before displaying it in the template."""

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

    return text


@register.filter
def highlight(text, phrase):
    """This filter higlights the specified phrase in the text."""

    # >>quote
    text = re.sub(
        r'(' + phrase + ')',
        r'<span class="highlight">\1</span>',
        text,
        flags=re.IGNORECASE
    )

    return text


@register.assignment_tag(takes_context=True)
def board_url_query_assign(context, *args, **kwargs):
    return board_url_query(context, *args, **kwargs)


@register.simple_tag(takes_context=True)
def board_url_query(context, *args, **kwargs):
    """This tag generates a query part of a board url.
    args[0] - name of the variable to replace
    args[1] - new value of the variable
    """
    # Create a shallow copy, otherwise this would overwrite the original values and break the following tags.
    parameters = copy.copy(context['parameters'])
    parameters['sort'] = parameters['sort_with_operator']

    # This tag does not have to overwrite values. Check if this behaviour is expected.
    if len(args) == 2:
        parameters[args[0]] = args[1]

    query =  format('?sort=%s&saved=%s&last_reply=%s&tagged=%s' % (
        parameters['sort'],
        parameters['saved'],
        parameters['last_reply'],
        parameters['tagged'],
    ))

    if parameters['tag'] is not None:
        query = format('%s&tag=%s' % (query, urllib.parse.quote('+'.join(parameters['tag']))))

    return query


@register.assignment_tag(takes_context=True)
def search_url_query_assign(context, *args, **kwargs):
    return search_url_query(context, *args, **kwargs)


@register.simple_tag(takes_context=True)
def search_url_query(context, *args, **kwargs):
    """This tag generates a query part of a board url.
    args[0] - name of the variable to replace
    args[1] - new value of the variable
    """
    # Create a shallow copy, otherwise this would overwrite the original values and break the following tags.
    parameters = copy.copy(context['parameters'])

    # This tag does not have to overwrite values. Check if this behaviour is expected.
    if len(args) == 2:
        parameters[args[0]] = args[1]

    query =  format('?saved=%s&age=%s&search=%s' % (
        parameters['saved'],
        parameters['age'],
        parameters['search'],
    ))

    return query
