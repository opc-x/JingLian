import { renderAnnotationPanel } from "../annotations-ui";
import { bindSpeakButtons } from "../audio";
import { esc } from "../esc";
import type {
  AnnotationBook,
  CategoryIndex,
  FaithfulBook,
  FaithfulLesson,
  FaithfulPage,
  PageAnnotation,
  VolumeIndex,
} from "../types";
import { renderCategoryTabs } from "./library";

function annFor(
  annotations: AnnotationBook,
  lessonId: number,
  pageNum: number
): PageAnnotation | undefined {
  return annotations.annotations.find(
    (a) => a.lessonId === lessonId && a.pageNum === pageNum
  );
}

export function renderReader(opts: {
  category: CategoryIndex;
  categories: CategoryIndex[];
  vol: VolumeIndex;
  book: FaithfulBook;
  lesson: FaithfulLesson;
  page: FaithfulPage;
  pageIndex: number;
  annotations: AnnotationBook;
}) {
  const { category, categories, vol, book, lesson, page, pageIndex, annotations } = opts;
  const ann = annFor(annotations, lesson.lessonId, page.pageNum);
  const total = lesson.pages.length;

  const bookOptions = category.books
    .map(
      (b) =>
        `<option value="${b.book}" ${b.book === vol.book ? "selected" : ""}>${esc(b.title)}</option>`
    )
    .join("");

  const lessonOptions = book.lessons
    .map(
      (l) =>
        `<option value="${l.lessonId}" ${l.lessonId === lesson.lessonId ? "selected" : ""}>Lesson ${l.lessonId}</option>`
    )
    .join("");

  return `
    <div class="reader-shell">
      <header class="reader-header">
        <a class="reader-back" href="#/library/${category.id}">← 书库</a>
        <nav class="cat-tabs cat-tabs-inline reader-cats">${renderCategoryTabs(categories, category.id, true)}</nav>
        <div class="reader-title">
          <select class="reader-select" id="book-jump">${bookOptions}</select>
          <select class="reader-select" id="lesson-jump">${lessonOptions}</select>
          <span class="reader-page-indicator">${pageIndex + 1} / ${total} 页</span>
        </div>
        <div class="reader-zoom">
          <button class="reader-nav-btn" id="zoom-out" type="button">−</button>
          <span class="zoom-label" id="zoom-label">100%</span>
          <button class="reader-nav-btn" id="zoom-in" type="button">+</button>
          <button class="reader-nav-btn" id="zoom-fit" type="button">整页</button>
        </div>
        <div class="reader-actions">
          <button class="reader-nav-btn" id="prev-page" type="button">上一页</button>
          <button class="reader-nav-btn primary" id="next-page" type="button">下一页</button>
        </div>
      </header>
      <div class="reader-body">
        <section class="reader-page" id="reader-scroll">
          <div class="reader-page-frame" id="page-frame">
            <img class="page-img" src="/${page.image}" alt="${esc(lesson.title)} p${page.pageNum}" />
          </div>
        </section>
        <aside class="reader-annotations">
          <div class="reader-ann-header"><div class="ai-badge">AI 批注</div></div>
          <div class="reader-ann-body">${renderAnnotationPanel(ann, book.book)}</div>
        </aside>
      </div>
    </div>`;
}

const ZOOM_KEY = "jingyu-page-zoom";
const ZOOM_MIN = 0.75;
const ZOOM_MAX = 2;
const ZOOM_STEP = 0.25;

function loadZoom() {
  const v = Number(sessionStorage.getItem(ZOOM_KEY));
  return v >= ZOOM_MIN && v <= ZOOM_MAX ? v : 1;
}

function applyZoom(mode: "width" | "fit", zoom: number) {
  const frame = document.getElementById("page-frame");
  const label = document.getElementById("zoom-label");
  const fitBtn = document.getElementById("zoom-fit");
  if (!frame) return;
  frame.classList.toggle("fit-screen", mode === "fit");
  if (mode === "width") {
    frame.style.setProperty("--page-zoom", String(zoom));
    if (label) label.textContent = `${Math.round(zoom * 100)}%`;
    if (fitBtn) fitBtn.textContent = "整页";
  } else {
    if (label) label.textContent = "整页";
    if (fitBtn) fitBtn.textContent = "放大";
  }
}

export function bindReader(opts: {
  onPrev: () => void;
  onNext: () => void;
  onLessonChange: (lessonId: number) => void;
  onBookChange: (bookNum: number) => void;
  onCategoryChange: (catId: string) => void;
}) {
  let zoom = loadZoom();
  let fitMode: "width" | "fit" = "width";
  applyZoom(fitMode, zoom);

  document.getElementById("zoom-in")?.addEventListener("click", () => {
    fitMode = "width";
    zoom = Math.min(ZOOM_MAX, zoom + ZOOM_STEP);
    sessionStorage.setItem(ZOOM_KEY, String(zoom));
    applyZoom(fitMode, zoom);
  });
  document.getElementById("zoom-out")?.addEventListener("click", () => {
    fitMode = "width";
    zoom = Math.max(ZOOM_MIN, zoom - ZOOM_STEP);
    sessionStorage.setItem(ZOOM_KEY, String(zoom));
    applyZoom(fitMode, zoom);
  });
  document.getElementById("zoom-fit")?.addEventListener("click", () => {
    fitMode = fitMode === "width" ? "fit" : "width";
    applyZoom(fitMode, zoom);
  });

  document.getElementById("prev-page")?.addEventListener("click", opts.onPrev);
  document.getElementById("next-page")?.addEventListener("click", opts.onNext);
  document.getElementById("lesson-jump")?.addEventListener("change", (e) => {
    opts.onLessonChange(Number((e.target as HTMLSelectElement).value));
  });
  document.getElementById("book-jump")?.addEventListener("change", (e) => {
    opts.onBookChange(Number((e.target as HTMLSelectElement).value));
  });
  document.querySelectorAll(".cat-tab").forEach((el) => {
    el.addEventListener("click", () => {
      const id = (el as HTMLElement).dataset.cat;
      if (id) opts.onCategoryChange(id);
    });
  });

  document.getElementById("reader-scroll")?.scrollTo(0, 0);
  bindSpeakButtons();

  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowLeft") opts.onPrev();
    if (e.key === "ArrowRight") opts.onNext();
  };
  window.removeEventListener("keydown", (window as unknown as { _rk?: typeof onKey })._rk!);
  (window as unknown as { _rk: typeof onKey })._rk = onKey;
  window.addEventListener("keydown", onKey);
}
