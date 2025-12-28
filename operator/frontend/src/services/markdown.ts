/**
 * Markdown rendering service - Safe rendering without vulnerabilities
 * No external markdown library; simple inline rendering
 */

interface MarkdownRenderResult {
    __html: string
}

function escapeHtml(text: string): string {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}

function sanitizeHtml(html: string): string {
    // Basic allowlist: only safe tags
    const allowedTags = ['p', 'strong', 'em', 'code', 'pre', 'br', 'li', 'ul', 'ol']
    const parser = new DOMParser()
    const doc = parser.parseFromString(`<div>${html}</div>`, 'text/html')

    const walker = doc.createTreeWalker(
        doc.body,
        NodeFilter.SHOW_ELEMENT,
        null
    )

    let node
    const nodesToRemove = []
    while ((node = walker.nextNode())) {
        if (!allowedTags.includes((node as Element).tagName.toLowerCase())) {
            nodesToRemove.push(node)
        }
    }

    nodesToRemove.forEach(n => n.parentNode?.removeChild(n))
    return doc.body.innerHTML
}

export function renderMarkdown(text: string): MarkdownRenderResult {
    // Basic patterns only
    let html = escapeHtml(text)

    // **bold** -> <strong>bold</strong>
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

    // _italic_ -> <em>italic</em>
    html = html.replace(/_(.+?)_/g, '<em>$1</em>')

    // `code` -> <code>code</code>
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

    // ```lang code block``` -> <pre><code>code</code></pre>
    html = html.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`
    })

    // newlines -> <br>
    html = html.replace(/\n/g, '<br>')

    // sanitize
    html = sanitizeHtml(html)

    return { __html: html }
}

export function extractCodeBlocks(text: string): { language: string; code: string }[] {
    const blocks = []
    const regex = /```([\w]*)\n([\s\S]*?)```/g
    let match

    while ((match = regex.exec(text)) !== null) {
        blocks.push({
            language: match[1] || 'text',
            code: match[2].trim(),
        })
    }

    return blocks
}
