import { esc } from "./esc";
import type { PageAnnotation, PatternItem } from "./types";

function hasContent(ann: PageAnnotation | undefined): boolean {
  if (!ann) return false;
  const b = ann.blocks;
  return !!(
    ann.summaryZh ||
    b?.vocab?.length ||
    b?.patterns?.length ||
    b?.grammar?.length ||
    b?.usage?.length
  );
}

function speakBtn(text: string, audio?: string) {
  const audioAttr = audio ? ` data-audio="/${audio}"` : "";
  return `<button class="speak-btn" type="button" data-speak="${esc(text)}"${audioAttr} title="发音">🔊</button>`;
}

function renderPattern(p: PatternItem) {
  const drills = p.drills?.length
    ? p.drills
    : p.examples?.length
      ? p.examples
      : [];
  const why = p.why ?? "";
  const when = p.when ?? "";
  const how = p.how ?? p.zh ?? "";

  return `<div class="pattern-card">
    <div class="pattern-head">
      <span class="pattern-en">${esc(p.en)}</span>
      ${speakBtn(p.en)}
      <span class="pattern-zh">${esc(p.zh)}</span>
    </div>
    <div class="wwh-grid">
      <div class="wwh-item"><span class="wwh-tag">Why</span><p>${esc(why || "—")}</p></div>
      <div class="wwh-item"><span class="wwh-tag">When</span><p>${esc(when || "—")}</p></div>
      <div class="wwh-item wwh-wide"><span class="wwh-tag">How</span><p>${esc(how)}</p></div>
    </div>
    ${
      drills.length
        ? `<div class="pattern-drills"><span class="wwh-tag">本页对练</span><ul>${drills.map((d) => `<li>${esc(d)}</li>`).join("")}</ul></div>`
        : ""
    }
    ${p.realLife ? `<div class="pattern-real"><span class="wwh-tag">实战</span><p>${esc(p.realLife)}</p></div>` : ""}
  </div>`;
}

export function renderAnnotationPanel(ann: PageAnnotation | undefined, bookNum: number) {
  if (!hasContent(ann)) {
    return `
      <div class="ai-ann-empty">
        <p><strong>AI 批注待生成</strong></p>
        <p class="muted"><code>python scripts/annotate_pages.py --book ${bookNum} --lesson 1 --force</code></p>
      </div>`;
  }

  const summary = ann?.summaryZh
    ? `<div class="ann-block ann-summary"><div class="ann-block-h">本页导读</div><p>${esc(ann.summaryZh)}</p></div>`
    : "";

  const patterns = ann?.blocks?.patterns?.length
    ? `<div class="ann-block ann-block-patterns">
        <div class="ann-block-h">① 句型 · Why / When / How</div>
        <p class="ann-block-desc muted">Callan 通过问答句练词——先懂句型框架，词在句里活起来。</p>
        ${ann.blocks.patterns.map(renderPattern).join("")}
      </div>`
    : "";

  const vocab = ann?.blocks?.vocab?.length
    ? `<div class="ann-block">
        <div class="ann-block-h">② 词汇 · 在句中练</div>
        <ul class="vocab-list">${ann.blocks.vocab
          .map(
            (v) => `<li class="vocab-item">
              <div class="vocab-main">
                <strong>${esc(v.word)}</strong>
                ${v.ipa ? `<span class="ipa">${esc(v.ipa)}</span>` : ""}
                ${speakBtn(v.word, v.audio)}
              </div>
              <div class="vocab-zh">${v.pos ? `<em>${esc(v.pos)}</em> ` : ""}${esc(v.zh)}</div>
              ${v.inDrill ? `<div class="vocab-drill">↳ ${esc(v.inDrill)}</div>` : ""}
            </li>`
          )
          .join("")}</ul>
      </div>`
    : "";

  const grammar = ann?.blocks?.grammar?.length
    ? `<div class="ann-block">
        <div class="ann-block-h">③ 语法</div>
        ${ann.blocks.grammar
          .map(
            (g) => `<div class="grammar-item"><strong>${esc(g.title)}</strong><p>${esc(g.body)}</p></div>`
          )
          .join("")}
      </div>`
    : "";

  const usage = ann?.blocks?.usage?.length
    ? `<div class="ann-block">
        <div class="ann-block-h">④ 实战运用</div>
        ${ann.blocks.usage
          .map(
            (u) => `<div class="usage-item"><strong>${esc(u.title)}</strong><p>${esc(u.body)}</p></div>`
          )
          .join("")}
      </div>`
    : "";

  const chart = ann?.chartRef
    ? `<div class="ann-chart-ref">📊 参见 Chart ${ann.chartRef}</div>`
    : "";

  return `${summary}${patterns}${vocab}${grammar}${usage}${chart}
    <div class="ai-policy">${ann?.generatedAt ? `生成于 ${esc(ann.generatedAt)}` : ""} · 目标：学完能开口用</div>`;
}
