import type { CategoryIndex, PathData } from "./types";
import { SITE } from "./config";

export function renderPathPage(path: PathData, category: CategoryIndex): string {
  const cefrColors: Record<string, string> = {
    A1: "#34d399",
    A2: "#38bdf8",
    B1: "#a78bfa",
    B2: "#fbbf24",
  };

  const levelCards = path.cefrLevels
    .map((lv) => {
      const color = cefrColors[lv.cefr] ?? "#8b9bb0";
      return `
      <div class="cefr-card" style="--cefr-color: ${color}">
        <div class="cefr-badge">${lv.cefr}</div>
        <h3>${lv.label}</h3>
        <p class="cefr-books">Book ${lv.books.join(" · ")}</p>
      </div>`;
    })
    .join("");

  const booksHtml = category.books
    .map((b) => {
      const color = cefrColors[b.cefr ?? "A1"] ?? "#8b9bb0";
      const nodes = path.nodes
        .filter((n) => n.book === b.book)
        .map((n) => {
          return `<button class="path-node" data-book="${n.book}" data-lesson="${n.lessonId}" style="--node-color: ${color}">
            <span class="node-id">L${n.lessonId}</span>
          </button>`;
        })
        .join("");
      return `
      <div class="path-book">
        <div class="path-book-header" style="--cefr-color: ${color}">
          <span class="cefr-pill">${b.cefr ?? "?"}</span>
          <strong>${b.title}</strong>
        </div>
        <div class="path-track">${nodes}</div>
      </div>`;
    })
    .join("");

  return `
    <main class="main path-page">
      <div class="hero">
        <div class="hero-eyebrow">${SITE.nameZh} · 学习路径</div>
        <h1>${category.title}</h1>
        <div class="hero-meta">点击节点直达课程</div>
      </div>
      <section class="path-section">
        <h2>CEFR</h2>
        <div class="cefr-grid">${levelCards}</div>
      </section>
      <section class="path-section">
        <h2>全书目录</h2>
        <div class="path-books">${booksHtml}</div>
      </section>
    </main>`;
}

export function bindPathEvents(
  onNavigate: (bookNum: number, lessonId: number) => void
) {
  document.querySelectorAll(".path-node").forEach((btn) => {
    btn.addEventListener("click", () => {
      const el = btn as HTMLElement;
      onNavigate(Number(el.dataset.book), Number(el.dataset.lesson));
    });
  });
}
