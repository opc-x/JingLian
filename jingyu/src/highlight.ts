/** 在问答句中高亮本块练习词项 */
export function highlightFocus(text: string, focusWords: string[]): string {
  if (!focusWords.length) return esc(text);
  let out = esc(text);
  const sorted = [...focusWords].sort((a, b) => b.length - a.length);
  for (const w of sorted) {
    if (w.length < 2) continue;
    const re = new RegExp(`\\b(${escapeReg(w)})\\b`, "gi");
    out = out.replace(re, '<mark class="focus-hit">$1</mark>');
  }
  return out;
}

function esc(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeReg(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
