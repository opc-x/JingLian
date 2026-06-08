import { SITE } from "../config";
import { esc } from "../esc";
import type { CategoryIndex, FaithfulCatalog } from "../types";
import { catalogCategories } from "../data";

const CEFR_COLOR: Record<string, string> = {
  A1: "#34d399",
  A2: "#38bdf8",
  B1: "#a78bfa",
  B2: "#fbbf24",
};

export function renderLibrary(catalog: FaithfulCatalog, activeCategoryId: string) {
  const categories = catalogCategories(catalog);
  const active =
    categories.find((c) => c.id === activeCategoryId) ?? categories[0];

  const tabs = categories
    .map((c) => {
      const on = c.id === active?.id ? "active" : "";
      return `<button class="cat-tab ${on}" data-cat="${c.id}" type="button">${esc(c.title)}</button>`;
    })
    .join("");

  const books = (active?.books ?? [])
    .map((b) => {
      const color = CEFR_COLOR[b.cefr ?? "A1"] ?? "#8b9bb0";
      const cover = b.coverImage
        ? `<img src="/${b.coverImage}" alt="" loading="lazy" />`
        : `<span class="lib-cover-fallback">${b.book}</span>`;

      return `
      <button class="lib-book-card" data-book="${b.book}" type="button">
        <div class="lib-book-cover" style="--cefr: ${color}">${cover}</div>
        <div class="lib-book-spine" style="--cefr: ${color}"></div>
        <div class="lib-book-info">
          <div class="lib-book-title">${esc(b.title)}</div>
          <div class="lib-book-meta">
            <span class="cefr-pill" style="--cefr-color: ${color}">${b.cefr ?? ""}</span>
            <span>${b.lessonCount} 课</span>
          </div>
        </div>
      </button>`;
    })
    .join("");

  return `
    <div class="site-shell lib-shell">
      <header class="lib-header">
        <div class="lib-brand">
          <div class="brand">${SITE.name}<span>Yu</span> <em>${SITE.nameZh}</em></div>
          <p class="lib-tagline">${SITE.tagline}</p>
        </div>
        <a class="header-link muted" href="#/path">学习路径</a>
      </header>

      <nav class="cat-tabs">${tabs}</nav>

      <main class="lib-main">
        <div class="lib-section-head">
          <div>
            <h1>${esc(active?.title ?? "书库")}</h1>
            <p class="muted">${esc(active?.subtitle ?? "")} · ${active?.bookCount ?? 0} 册 · ${active?.lessonCount ?? 0} 课</p>
          </div>
        </div>
        <div class="lib-shelf">
          <div class="lib-shelf-edge"></div>
          <div class="lib-book-grid">${books}</div>
        </div>
      </main>
    </div>`;
}

export function bindLibrary(
  onSwitchCategory: (id: string) => void,
  onOpenBook: (bookNum: number) => void
) {
  document.querySelectorAll(".cat-tab").forEach((el) => {
    el.addEventListener("click", () => {
      const id = (el as HTMLElement).dataset.cat;
      if (id) onSwitchCategory(id);
    });
  });
  document.querySelectorAll(".lib-book-card").forEach((el) => {
    el.addEventListener("click", () => {
      onOpenBook(Number((el as HTMLElement).dataset.book));
    });
  });
}

export function renderCategoryTabs(
  categories: CategoryIndex[],
  activeId: string,
  compact = false
) {
  return categories
    .map((c) => {
      const on = c.id === activeId ? "active" : "";
      const cls = compact ? "cat-tab cat-tab-sm" : "cat-tab";
      return `<button class="${cls} ${on}" data-cat="${c.id}" type="button">${esc(c.title)}</button>`;
    })
    .join("");
}
