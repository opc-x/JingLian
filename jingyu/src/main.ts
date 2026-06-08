import "./style.css";
import {
  catalogCategories,
  findCategory,
  findVolume,
  loadAnnotations,
  loadCatalog,
  loadPath,
  loadVolumeBook,
} from "./data";
import { esc } from "./esc";
import { bindPathEvents, renderPathPage } from "./path";
import { parseHash, saveCategory, setRoute, type Route } from "./router";
import type { FaithfulBook, FaithfulCatalog, FaithfulLesson, PathData } from "./types";
import { bindTocPage, renderTocPage } from "./views/book";
import { bindLibrary, renderLibrary } from "./views/library";
import { bindReader, renderReader } from "./views/reader";

const app = document.getElementById("app")!;

let catalog: FaithfulCatalog | null = null;
let pathData: PathData | null = null;
let book: FaithfulBook | null = null;
let route: Route = { screen: "library" };

function activeCategory() {
  if (!catalog) return undefined;
  const cats = catalogCategories(catalog);
  const id = route.categoryId ?? cats[0]?.id;
  return id ? findCategory(catalog, id) : cats[0];
}

function currentLesson(): FaithfulLesson | undefined {
  if (!book) return undefined;
  if (!route.lessonId) return book.lessons[0];
  return book.lessons.find((l) => l.lessonId === route.lessonId) ?? book.lessons[0];
}

function lessonIndex(lesson: FaithfulLesson) {
  return book!.lessons.findIndex((l) => l.lessonId === lesson.lessonId);
}

function pageIndexInLesson(lesson: FaithfulLesson) {
  if (route.pageNum != null) {
    const idx = lesson.pages.findIndex((p) => p.pageNum === route.pageNum);
    if (idx >= 0) return idx;
  }
  return 0;
}

async function navigate(next: Route) {
  route = next;
  setRoute(route);
  await render();
}

async function render() {
  if (!catalog) return;
  const cats = catalogCategories(catalog);
  const category = activeCategory();

  if (route.screen === "library") {
    app.className = "app-full";
    const catId = category?.id ?? cats[0]?.id ?? "";
    app.innerHTML = renderLibrary(catalog, catId);
    bindLibrary(
      (id) => navigate({ screen: "library", categoryId: id }),
      (bookNum) => {
        saveCategory(catId);
        navigate({ screen: "toc", categoryId: catId, bookNum });
      }
    );
    return;
  }

  if (route.screen === "path") {
    app.className = "app-full";
    if (!pathData || !category) {
      app.innerHTML = `<div class="empty">路径数据未加载</div>`;
      return;
    }
    app.innerHTML = `
      <div class="site-shell">
        <header class="site-header site-header-min">
          <a class="brand-link" href="#/library/${category.id}"><div class="brand">← 书库</div></a>
        </header>
        ${renderPathPage(pathData, category)}
      </div>`;
    bindPathEvents((bookNum, lessonId) => {
      navigate({ screen: "reader", categoryId: category.id, bookNum, lessonId });
    });
    return;
  }

  if (!category) {
    await navigate({ screen: "library" });
    return;
  }

  const vol = route.bookNum ? findVolume(category, route.bookNum) : undefined;
  if (!vol) {
    await navigate({ screen: "library", categoryId: category.id });
    return;
  }

  if (route.screen === "toc") {
    app.className = "app-full";
    app.innerHTML = `<div class="loading">加载 ${vol.title}…</div>`;
    book = await loadVolumeBook(vol);
    app.innerHTML = renderTocPage(category, cats, vol, book);
    bindTocPage(
      (lessonId) =>
        navigate({ screen: "reader", categoryId: category.id, bookNum: vol.book, lessonId }),
      (bookNum) => navigate({ screen: "toc", categoryId: category.id, bookNum }),
      (catId) => navigate({ screen: "library", categoryId: catId })
    );
    return;
  }

  if (route.screen === "reader") {
    app.className = "app-reader";
    if (!book || book.book !== vol.book) {
      book = await loadVolumeBook(vol);
    }
    const lesson = currentLesson();
    if (!lesson) {
      app.innerHTML = `<div class="empty">无课文</div>`;
      return;
    }
    const annotations = await loadAnnotations(vol.book);
    const pageIdx = pageIndexInLesson(lesson);
    const page = lesson.pages[pageIdx];
    if (!page) {
      app.innerHTML = `<div class="empty">无页面</div>`;
      return;
    }

    const lesIdx = lessonIndex(lesson);

    app.innerHTML = renderReader({
      category,
      categories: cats,
      vol,
      book,
      lesson,
      page,
      pageIndex: pageIdx,
      annotations,
    });

    bindReader({
      onPrev: () => {
        if (pageIdx > 0) {
          navigate({
            screen: "reader",
            categoryId: category.id,
            bookNum: vol.book,
            lessonId: lesson.lessonId,
            pageNum: lesson.pages[pageIdx - 1].pageNum,
          });
        } else if (lesIdx > 0) {
          const prev = book!.lessons[lesIdx - 1];
          navigate({
            screen: "reader",
            categoryId: category.id,
            bookNum: vol.book,
            lessonId: prev.lessonId,
            pageNum: prev.pages[prev.pages.length - 1].pageNum,
          });
        }
      },
      onNext: () => {
        if (pageIdx < lesson.pages.length - 1) {
          navigate({
            screen: "reader",
            categoryId: category.id,
            bookNum: vol.book,
            lessonId: lesson.lessonId,
            pageNum: lesson.pages[pageIdx + 1].pageNum,
          });
        } else if (lesIdx < book!.lessons.length - 1) {
          const next = book!.lessons[lesIdx + 1];
          navigate({
            screen: "reader",
            categoryId: category.id,
            bookNum: vol.book,
            lessonId: next.lessonId,
          });
        }
      },
      onLessonChange: (lessonId) => {
        navigate({ screen: "reader", categoryId: category.id, bookNum: vol.book, lessonId });
      },
      onBookChange: (bookNum) => {
        navigate({ screen: "reader", categoryId: category.id, bookNum, lessonId: 1 });
      },
      onCategoryChange: (catId) => {
        navigate({ screen: "library", categoryId: catId });
      },
    });
    return;
  }

  await navigate({ screen: "library", categoryId: category.id });
}

async function init() {
  app.className = "app-full";
  app.innerHTML = `<div class="loading">加载书库…</div>`;
  try {
    catalog = await loadCatalog();
    pathData = await loadPath();
    route = parseHash();
    window.addEventListener("hashchange", async () => {
      route = parseHash();
      await render();
    });
    await render();
  } catch (e) {
    app.innerHTML = `<div class="empty">${esc(String(e))}<br/><code>./scripts/run_all.sh</code></div>`;
  }
}

init();
