import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

interface ChatMessageProps {
  content: string
  role: 'user' | 'assistant'
}

const mdComponents: Components = {
  table: ({ children, ...props }) => (
    <div style={{ overflowX: 'auto', margin: '12px 0' }}>
      <table
        {...props}
        style={{
          width: '100%',
          borderCollapse: 'separate',
          borderSpacing: 0,
          borderRadius: 8,
          overflow: 'hidden',
          fontSize: 13,
        }}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead
      {...props}
      style={{
        background: 'var(--bg-surface)',
      }}
    >
      {children}
    </thead>
  ),
  th: ({ children, ...props }) => (
    <th
      {...props}
      style={{
        padding: '10px 14px',
        fontWeight: 600,
        fontSize: 12,
        textTransform: 'uppercase',
        letterSpacing: '0.03em',
        color: 'var(--text-secondary)',
        borderBottom: '2px solid var(--border-light)',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td
      {...props}
      style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--border-light)',
        color: 'var(--text-primary)',
      }}
    >
      {children}
    </td>
  ),
  tr: ({ children, ...props }) => (
    <tr
      {...props}
      style={{ transition: 'background 0.15s' }}
      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      {children}
    </tr>
  ),
  strong: ({ children, ...props }) => (
    <strong {...props} style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
      {children}
    </strong>
  ),
  h1: ({ children }) => (
    <h4 style={{ margin: '16px 0 8px', fontWeight: 700, color: 'var(--text-primary)' }}>{children}</h4>
  ),
  h2: ({ children }) => (
    <h5 style={{ margin: '14px 0 6px', fontWeight: 700, color: 'var(--text-primary)' }}>{children}</h5>
  ),
  h3: ({ children }) => (
    <h6 style={{ margin: '12px 0 4px', fontWeight: 700, color: 'var(--text-primary)' }}>{children}</h6>
  ),
  ul: ({ children }) => (
    <ul style={{ paddingLeft: 20, margin: '8px 0' }}>{children}</ul>
  ),
  ol: ({ children }) => (
    <ol style={{ paddingLeft: 20, margin: '8px 0' }}>{children}</ol>
  ),
  li: ({ children }) => (
    <li style={{ marginBottom: 4, lineHeight: 1.6 }}>{children}</li>
  ),
  p: ({ children }) => (
    <p style={{ margin: '6px 0', lineHeight: 1.6 }}>{children}</p>
  ),
  code: ({ children, className }) => {
    const isBlock = className?.includes('language-')
    if (isBlock) {
      return (
        <pre
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-light)',
            borderRadius: 6,
            padding: '12px 16px',
            margin: '8px 0',
            overflowX: 'auto',
            fontSize: 13,
          }}
        >
          <code style={{ color: 'var(--text-primary)' }}>{children}</code>
        </pre>
      )
    }
    return (
      <code
        style={{
          background: 'var(--bg-surface)',
          padding: '2px 6px',
          borderRadius: 4,
          fontSize: 13,
          color: 'var(--text-primary)',
        }}
      >
        {children}
      </code>
    )
  },
  blockquote: ({ children }) => (
    <blockquote
      style={{
        borderLeft: '3px solid var(--border-light)',
        paddingLeft: 12,
        margin: '8px 0',
        color: 'var(--text-secondary)',
        fontStyle: 'italic',
      }}
    >
      {children}
    </blockquote>
  ),
  hr: () => (
    <hr style={{ border: 'none', borderTop: '1px solid var(--border-light)', margin: '12px 0' }} />
  ),
}

export function ChatMessage({ content, role }: ChatMessageProps) {
  if (role === 'user') {
    return <span>{content}</span>
  }

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
      {content}
    </ReactMarkdown>
  )
}
