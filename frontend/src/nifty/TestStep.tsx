import React, { useMemo } from 'react';
import { ArrowRight, TriangleAlert } from 'lucide-react';
import type { NiftyRunResponse } from './types';
import { formatPct, formatPrice, formatWinRate } from './format';

interface TestStepProps {
  run: NiftyRunResponse;
  onExplain: () => void;
  onBack: () => void;
  explainLoading: boolean;
}

function Histogram({ values }: { values: number[] }) {
  const bins = useMemo(() => {
    if (values.length === 0) return [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const n = 12;
    const span = max - min || 1e-9;
    const counts = new Array(n).fill(0) as number[];
    for (const v of values) {
      const idx = Math.min(n - 1, Math.floor(((v - min) / span) * n));
      counts[idx] += 1;
    }
    const peak = Math.max(...counts, 1);
    return counts.map((c, i) => ({
      count: c,
      heightPct: Math.max(4, (c / peak) * 100),
      low: min + (span * i) / n,
      high: min + (span * (i + 1)) / n,
    }));
  }, [values]);
  if (values.length === 0) {
    return <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No trades — nothing to distribute.</div>;
  }
  return (
    <div>
      <div
        aria-label="Distribution of primary holding net returns"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '72px' }}
      >
        {bins.map((b, i) => (
          <div
            key={i}
            title={`${formatPct(b.low)} to ${formatPct(b.high)}: ${b.count} trade(s)`}
            style={{
              flex: 1,
              height: `${b.heightPct}%`,
              backgroundColor: 'var(--color-primary-bg)',
              border: '1px solid var(--color-primary-border)',
              borderRadius: '3px 3px 0 0',
              minWidth: '6px',
            }}
          />
        ))}
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
        Primary-hold net-return distribution (n={values.length}). Each bar is a return bucket.
      </div>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-surface)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-md)',
  padding: '12px 16px',
};

export const TestStep: React.FC<TestStepProps> = ({ run, onExplain, onBack, explainLoading }) => {
  const primaryReturns = run.returns_by_holding[String(run.primary.holding_days)] ?? run.returns_by_holding[run.primary.holding_days] ?? [];
  const shownTrades = run.trades.slice(0, 25);
  const empty = run.primary.trade_count === 0 || run.primary.average_net_return === null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div
        style={{
          backgroundColor: 'var(--color-warning-bg)',
          border: '1px solid var(--color-warning-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '12px 16px',
          fontSize: '12px',
          color: 'var(--color-warning)',
          display: 'flex',
          gap: '8px',
          alignItems: 'flex-start',
        }}
      >
        <TriangleAlert size={15} style={{ flexShrink: 0, marginTop: '1px' }} />
        <span>
          <strong>Synthetic mock data</strong> — {run.dataset.source_note} Coverage{' '}
          {run.dataset.coverage_start} → {run.dataset.coverage_end} ({run.dataset.rows_in_period} rows in period).
          Historical observation only; not evidence about future performance.
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
        <div style={cardStyle}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Signals detected</div>
          <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700 }}>{run.signals_detected}</div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Primary trades ({run.primary.holding_days}d)</div>
          <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700 }}>{run.primary.trade_count}</div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Avg net return</div>
          <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700 }}>{formatPct(run.primary.average_net_return)}</div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Median net return</div>
          <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700 }}>{formatPct(run.primary.median_net_return)}</div>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Win rate</div>
          <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700 }}>{formatWinRate(run.primary.win_rate)}</div>
        </div>
      </div>

      {run.warnings.length > 0 && (
        <div
          style={{
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            padding: '14px 18px',
          }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>Warnings</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--color-warning)' }}>
            {run.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 18px',
        }}
      >
        <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Sensitivity — holding-period comparison</h3>
        <table>
          <thead>
            <tr>
              <th>Holding</th>
              <th>Trades</th>
              <th>Avg net</th>
              <th>Median net</th>
              <th>Win rate</th>
            </tr>
          </thead>
          <tbody className="font-mono" style={{ fontSize: '12px' }}>
            <tr style={{ backgroundColor: 'var(--color-primary-bg)' }}>
              <td>{run.primary.holding_days}d (primary)</td>
              <td>{run.primary.trade_count}</td>
              <td>{formatPct(run.primary.average_net_return)}</td>
              <td>{formatPct(run.primary.median_net_return)}</td>
              <td>{formatWinRate(run.primary.win_rate)}</td>
            </tr>
            {run.sensitivity.map((s) => (
              <tr key={s.holding_days}>
                <td>{s.holding_days}d</td>
                <td>{s.trade_count}</td>
                <td>{formatPct(s.average_net_return)}</td>
                <td>{formatPct(s.median_net_return)}</td>
                <td>{formatWinRate(s.win_rate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: '14px' }}>
          <Histogram values={primaryReturns} />
        </div>
      </div>

      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 18px',
          overflowX: 'auto',
        }}
      >
        <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
          Trade-level evidence (primary hold{empty ? ' — none' : `, showing ${shownTrades.length} of ${run.trades.length}`})
        </h3>
        {empty ? (
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            No complete {run.primary.holding_days}-day trade could be formed under these assumptions. No conclusion
            can be drawn — the LEARN step will state this explicitly.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Signal</th>
                <th>Entry (next open)</th>
                <th>Exit</th>
                <th>Entry price</th>
                <th>Exit price</th>
                <th>Net return</th>
              </tr>
            </thead>
            <tbody className="font-mono" style={{ fontSize: '12px' }}>
              {shownTrades.map((t) => (
                <tr key={`${t.signal_date}-${t.entry_date}`}>
                  <td>{t.signal_date}</td>
                  <td>{t.entry_date}</td>
                  <td>{t.exit_date}</td>
                  <td>{formatPrice(t.entry_price)}</td>
                  <td>{formatPrice(t.exit_price)}</td>
                  <td>{formatPct(t.net_return)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={onBack}
          style={{
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          Back to DEFINE
        </button>
        <button
          type="button"
          onClick={onExplain}
          disabled={explainLoading}
          style={{
            backgroundColor: 'var(--color-primary)',
            color: '#030712',
            borderRadius: 'var(--radius-md)',
            padding: '8px 20px',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {explainLoading ? 'Summarizing…' : 'Continue to LEARN'}
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};
