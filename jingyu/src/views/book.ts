import { esc } from "../esc";
import type { CategoryIndex, FaithfulBook, VolumeIndex } from "../types";
import { renderCategoryTabs } from "./library";

export function renderTocPage(
  category: CategoryIndex,
  categories: CategoryIndex[],
  vol: VolumeIndex,
  book: FaithfulBook
) {
  const lessons = book.lessons
    .map((l) => {
      return `
      <button class="lesson-row" data-lesson="${l.lessonId}" type="button">
        <span class="lesson-row-no">${l.lessonId}</span>
        <span class="lesson-row-info">
          <span class="lesson-row-title">${esc(l.title)}</span>
          <span class="lesson-row-meta">${l.pageCount} 页</span>
        </span>
        <span class="lesson-row-arrow">→</span>
      </button>`;
    })
    .join("");

  const bookOptions = category.books
    .map(
      (b) =>
        `<option value="${b.book}" ${b.book === vol.book ? "selected" : ""}>${esc(b.title)} · ${b.cefr ?? ""}</option>`
    )
    .join("");

  return `
    <div class="site-shell">
      <header class="site-header site-header-min">
        <a class="brand-link" href="#/library/${category.id}"><div class="brand">← 书库</div></a>
        <nav class="cat-tabs cat-tabs-inline">${renderCategoryTabs(categories, category.id, true)}</nav>
      </header>
      <main class="list-main">
        <div class="list-hero">
          <div class="toc-book-switch">
            <select class="reader-lesson-select" id="book-jump">${bookOptions}</select>
          </div>
          <h1>${esc(vol.title)}</h1>
          <p class="muted">CEFR ${esc(book.cefr)} · ${book.lessonCount} 课</p>
          <button class="primary-btn" id="start-first" data-lesson="${book.lessons[0]?.lessonId ?? 1}" type="button">
            从第 1 课开始读 →
          </button>
        </div>
        <div class="lesson-list-flat">${lessons}</div>
      </main>
    </div>`;
}

export function bindTocPage(
  onRead: (lessonId: number) => void,
  onBookChange: (bookNum: number) => void,
  onCategoryChange: (catId: string) => void
) {
  document.querySelectorAll(".lesson-row").forEach((btn) => {
    btn.addEventListener("click", () => {
      onRead(Number((btn as HTMLElement).dataset.lesson));
    });
  });
  document.getElementById("start-first")?.addEventListener("click", () => {
    const el = document.getElementById("start-first") as HTMLElement;
    onRead(Number(el.dataset.lesson));
  });
  document.getElementById("book-jump")?.addEventListener("change", (e) => {
    onBookChange(Number((e.target as HTMLSelectElement).value));
  });
  document.querySelectorAll(".cat-tab").forEach((el) => {
    el.addEventListener("click", () => {
      const id = (el as HTMLElement).dataset.cat;
      if (id) onCategoryChange(id);
    });
  });
}
