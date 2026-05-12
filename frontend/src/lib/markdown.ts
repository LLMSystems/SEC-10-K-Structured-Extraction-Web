import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: true, // allow embedded HTML (notably <table>)
  linkify: true,
  breaks: false,
  typographer: false,
})

// Open links in new tab + harden rel.
const defaultLinkOpen =
  md.renderer.rules.link_open ??
  function (tokens, idx, options, _env, self) {
    return self.renderToken(tokens, idx, options)
  }
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (token) {
    const targetIdx = token.attrIndex('target')
    if (targetIdx < 0) token.attrPush(['target', '_blank'])
    else token.attrs![targetIdx]![1] = '_blank'
    const relIdx = token.attrIndex('rel')
    if (relIdx < 0) token.attrPush(['rel', 'noopener noreferrer'])
    else token.attrs![relIdx]![1] = 'noopener noreferrer'
  }
  return defaultLinkOpen(tokens, idx, options, env, self)
}

const PURIFY_CONFIG = {
  USE_PROFILES: { html: true },
  ADD_ATTR: ['target', 'rel', 'colspan', 'rowspan', 'align', 'valign', 'scope'],
  FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed'],
  FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick'],
}

export function renderMarkdown(source: string): string {
  if (!source) return ''
  const raw = md.render(source)
  return DOMPurify.sanitize(raw, PURIFY_CONFIG) as unknown as string
}
