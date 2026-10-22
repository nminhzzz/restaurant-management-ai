const RECEIPT_STYLE = `
  body { font-family: ui-sans-serif, system-ui, sans-serif; color: #111; margin: 0; padding: 16px; }
  h1 { font-size: 16px; margin: 0 0 4px; }
  .muted { color: #666; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }
  th, td { text-align: left; padding: 4px 0; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .total { display: flex; justify-content: space-between; border-top: 1px solid #ccc; margin-top: 8px; padding-top: 8px; font-weight: 700; }
  .notice { border: 1px solid #111; padding: 6px; margin-bottom: 10px; font-weight: 700; text-align: center; }
  pre { white-space: pre-wrap; font-size: 12px; }
`;

export function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/** Open a print-ready window; returns false when the browser blocked it. */
export function printDocument(title: string, bodyHtml: string): boolean {
  const win = window.open("", "_blank", "width=420,height=640");
  if (!win) return false;
  win.document.write(
    `<!doctype html><html lang="vi"><head><meta charset="utf-8" />` +
      `<title>${escapeHtml(title)}</title><style>${RECEIPT_STYLE}</style></head>` +
      `<body>${bodyHtml}</body></html>`,
  );
  win.document.close();
  win.focus();
  win.print();
  return true;
}
