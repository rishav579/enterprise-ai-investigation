/** Pure display helpers for NIFTY metrics. No backend logic duplicated. */

/** Format a decimal fraction (e.g. 0.0123) as +1.23%. Null -> '—'. */
export function formatPct(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—';
  const sign = x > 0 ? '+' : '';
  return `${sign}${(x * 100).toFixed(2)}%`;
}

/** Format win rate fraction (0..1) as 62.5%. Null -> '—'. */
export function formatWinRate(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—';
  return `${(x * 100).toFixed(1)}%`;
}

/** Format a price with 2 decimals. */
export function formatPrice(x: number): string {
  return x.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Short human label for a workflow stage. */
export function stageLabel(stage: string): string {
  switch (stage) {
    case 'ask':
      return 'ASK';
    case 'clarify':
      return 'CLARIFY';
    case 'define':
      return 'DEFINE';
    case 'test':
      return 'TEST';
    case 'learn':
      return 'LEARN';
    default:
      return stage;
  }
}
