export type Screen = "library" | "toc" | "reader" | "path";

export interface Route {
  screen: Screen;
  categoryId?: string;
  bookNum?: number;
  lessonId?: number;
  pageNum?: number;
}

const CAT_KEY = "jingyu-category";

export function getSavedCategory(): string | null {
  return sessionStorage.getItem(CAT_KEY);
}

export function saveCategory(id: string) {
  sessionStorage.setItem(CAT_KEY, id);
}

export function parseHash(): Route {
  const raw = location.hash.replace(/^#\/?/, "") || "library";
  const parts = raw.split("/").filter(Boolean);

  if (parts[0] === "path") return { screen: "path" };

  if (parts[0] === "library" || parts.length === 0) {
    const categoryId = parts[1] || getSavedCategory() || undefined;
    return { screen: "library", categoryId };
  }

  // 兼容旧链接 #/series/callan-method/book/12/...
  if (parts[0] === "series") {
    const categoryId = parts[1];
    if (parts[2] === "book") {
      const bookNum = Number(parts[3]);
      if (parts[4] === "read") {
        const lessonId = Number(parts[5]) || 1;
        const pIdx = parts.indexOf("p");
        const pageNum = pIdx >= 0 ? Number(parts[pIdx + 1]) : undefined;
        return { screen: "reader", categoryId, bookNum, lessonId, pageNum };
      }
      return { screen: "toc", categoryId, bookNum };
    }
    return { screen: "library", categoryId };
  }

  if (parts[0] === "book") {
    const bookNum = Number(parts[1]);
    if (!bookNum) return { screen: "library" };
    const categoryId = getSavedCategory() || undefined;

    if (parts[2] === "read") {
      const lessonId = Number(parts[3]) || 1;
      const pIdx = parts.indexOf("p");
      const pageNum = pIdx >= 0 ? Number(parts[pIdx + 1]) : undefined;
      return { screen: "reader", categoryId, bookNum, lessonId, pageNum };
    }
    return { screen: "toc", categoryId, bookNum };
  }

  return { screen: "library" };
}

export function setRoute(route: Route) {
  let hash = "#/library";
  if (route.categoryId) {
    hash = `#/library/${route.categoryId}`;
    saveCategory(route.categoryId);
  }
  if (route.screen === "path") hash = "#/path";
  else if (route.screen === "toc" && route.bookNum)
    hash = `#/book/${route.bookNum}`;
  else if (route.screen === "reader" && route.bookNum) {
    hash = `#/book/${route.bookNum}/read/${route.lessonId ?? 1}`;
    if (route.pageNum != null) hash += `/p/${route.pageNum}`;
  }
  if (location.hash !== hash) location.hash = hash;
}
