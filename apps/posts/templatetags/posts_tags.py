"""
Template-Filter der Posts-App (Task 5.2, FR-B3, D-80; Task 6.4, FR-B17).

`markdown` ist die einzige Stelle in den Templates, an der Nutzertext als
`safe` ausgegeben wird (ARCHITECTURE §7); `excerpt` und `comment_excerpt`
liefern Klartext, den Djangos Autoescape wie jeden Text behandelt.
"""

from django import template

from apps.posts import listing
from apps.posts import markdown as post_markdown

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(value):
    return post_markdown.render_markdown(value)


@register.filter(name="excerpt")
def excerpt_filter(value, limit=post_markdown.EXCERPT_LENGTH):
    return post_markdown.excerpt(value, int(limit))


@register.filter(name="comment_excerpt")
def comment_excerpt_filter(value):
    """Klartext-Auszug eines Kommentars (Task 6.4) — kein `limit`-Argument wie
    bei `excerpt`: Kommentare sind schon Klartext, eine Länge reicht."""
    return listing.comment_excerpt(value)
