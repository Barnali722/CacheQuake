/**
 * ErrorBoundary.jsx
 * Catches render-time errors so a crash in one component doesn't blank the whole app.
 */
import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          padding: '24px', background: '#1a0000', color: '#ff6b6b',
          fontFamily: 'monospace', fontSize: '13px', margin: '16px',
          border: '1px solid #ff6b6b', borderRadius: '6px',
        }}>
          <strong>⚠ Component Error:</strong>
          <pre style={{ marginTop: '8px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {this.state.error.message}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              marginTop: '12px', padding: '6px 16px', background: '#3a0000',
              border: '1px solid #ff6b6b', color: '#ff6b6b', cursor: 'pointer',
              borderRadius: '4px', fontFamily: 'inherit',
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
