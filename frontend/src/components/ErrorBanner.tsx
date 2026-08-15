import React from 'react';
import { AlertCircle, XCircle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  error: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onDismiss, onRetry }) => {
  return (
    <div style={{
      backgroundColor: 'var(--color-danger-bg)',
      border: '1px solid var(--color-danger-border)',
      borderRadius: 'var(--radius-lg)',
      padding: '14px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px',
      color: 'var(--color-danger)',
      fontSize: '13px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
        <AlertCircle size={18} style={{ flexShrink: 0 }} />
        <span style={{ fontWeight: 500 }}>{error}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            style={{
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--color-danger-border)',
              color: 'var(--color-danger)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <RefreshCw size={11} /> Retry
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-danger)',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
            }}
            aria-label="Dismiss error"
          >
            <XCircle size={16} />
          </button>
        )}
      </div>
    </div>
  );
};
