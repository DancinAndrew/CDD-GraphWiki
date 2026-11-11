import React from 'react';
import { Highlight } from './explanationTypes';

interface MergedSpan {
  start: number;
  end: number;
  rules: string[];
}

// 片段是 raw_text 的字元位移（code point）；先排除越界的，再把重疊的合併成一段
export const mergeHighlights = (highlights: Highlight[], length: number): MergedSpan[] => {
  const valid = highlights
    .filter((h) => h.start >= 0 && h.end <= length && h.start < h.end)
    .sort((a, b) => a.start - b.start || a.end - b.end);
  const merged: MergedSpan[] = [];
  for (const h of valid) {
    const last = merged[merged.length - 1];
    if (last && h.start < last.end) {
      last.end = Math.max(last.end, h.end);
      for (const rule of h.rules) if (!last.rules.includes(rule)) last.rules.push(rule);
    } else {
      merged.push({ start: h.start, end: h.end, rules: [...h.rules] });
    }
  }
  return merged;
};

interface HighlightedTextProps {
  text: string;
  highlights: Highlight[];
}

// 後端的位移以 Unicode code point 計（Python 字串索引），JavaScript 字串以 UTF-16 計：
// 回傳每個 code point 位置對應的 UTF-16 索引（長度為 code point 數 + 1）
export const codePointToUtf16 = (text: string): number[] => {
  const offsets = [0];
  for (const char of Array.from(text)) offsets.push(offsets[offsets.length - 1] + char.length);
  return offsets;
};

export const HighlightedText: React.FC<HighlightedTextProps> = ({ text, highlights }) => {
  const utf16 = codePointToUtf16(text);
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  // 合併在 code point 座標上進行，切字串前才換成 UTF-16 索引
  for (const span of mergeHighlights(highlights, utf16.length - 1)) {
    const start = utf16[span.start];
    const end = utf16[span.end];
    if (start > cursor) nodes.push(text.slice(cursor, start));
    nodes.push(
      <mark key={span.start} title={span.rules.join(', ')} style={markStyle}>
        {text.slice(start, end)}
      </mark>
    );
    cursor = end;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return <>{nodes}</>;
};

export const markStyle: React.CSSProperties = {
  background: 'rgba(255, 179, 0, 0.25)',
  color: '#fde68a',
  borderRadius: '3px',
  padding: '0 2px',
};
