import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = (rel: string) => [
  path.resolve(process.cwd(), `../data/${rel}`),
  path.resolve(here, `../../../data/${rel}`),
];

export interface Comparison {
  label: string;
  value: number | null;
  zone: string;
  date: string;
}
export interface Reading {
  source: string;
  value: number;
  zone: string;
  ts: string;
  source_date: string;
  raw: number | null;
  nifty: number | null;
  vix: number | null;
  fii: number | null;
  comparisons: Comparison[];
  summary: string;
}
export interface HistPoint {
  ts: string;
  value: number;
  zone: string;
}

const EMPTY: Reading = {
  source: '',
  value: 0,
  zone: 'Extreme Fear',
  ts: '',
  source_date: '',
  raw: null,
  nifty: null,
  vix: null,
  fii: null,
  comparisons: [],
  summary: '',
};

function readFirst(candidates: string[]): string | null {
  for (const p of candidates) {
    try {
      return fs.readFileSync(p, 'utf-8');
    } catch {
      /* next */
    }
  }
  return null;
}

export function loadReading(): Reading {
  const raw = readFirst(dataDir('latest.json'));
  if (!raw) return EMPTY;
  try {
    return { ...EMPTY, ...JSON.parse(raw) };
  } catch {
    return EMPTY;
  }
}

/** Merge every history/<date>.json into one time-ordered series for the sparkline. */
export function loadHistory(): HistPoint[] {
  const dirs = [
    path.resolve(process.cwd(), '../data/history'),
    path.resolve(here, '../../../data/history'),
  ];
  for (const dir of dirs) {
    try {
      const files = fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort();
      const pts: HistPoint[] = [];
      for (const f of files) {
        try {
          const arr = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8'));
          if (Array.isArray(arr)) pts.push(...arr);
        } catch {
          /* skip */
        }
      }
      pts.sort((a, b) => a.ts.localeCompare(b.ts));
      return pts;
    } catch {
      /* next dir */
    }
  }
  return [];
}
