import type {
  AnnotationBook,
  CategoryIndex,
  FaithfulBook,
  FaithfulCatalog,
  PathData,
  VolumeIndex,
} from "./types";

let catalogCache: FaithfulCatalog | null = null;
const bookCache = new Map<string, FaithfulBook>();
const annCache = new Map<number, AnnotationBook>();

export function catalogCategories(catalog: FaithfulCatalog): CategoryIndex[] {
  return catalog.categories ?? catalog.series ?? [];
}

export async function loadCatalog(): Promise<FaithfulCatalog> {
  if (catalogCache) return catalogCache;
  const res = await fetch("/faithful/index.json");
  if (!res.ok) throw new Error("无法加载书库，请先运行 ./scripts/run_all.sh");
  catalogCache = await res.json();
  return catalogCache;
}

export function findCategory(
  catalog: FaithfulCatalog,
  id: string
): CategoryIndex | undefined {
  return catalogCategories(catalog).find((c) => c.id === id);
}

export function findVolume(cat: CategoryIndex, bookNum: number): VolumeIndex | undefined {
  return cat.books.find((b) => b.book === bookNum);
}

export async function loadVolumeBook(vol: VolumeIndex): Promise<FaithfulBook> {
  const key = vol.file;
  if (bookCache.has(key)) return bookCache.get(key)!;
  const res = await fetch(`/faithful/${vol.file.replace("faithful/", "")}`);
  if (!res.ok) throw new Error(`无法加载 ${vol.file}`);
  const data: FaithfulBook = await res.json();
  bookCache.set(key, data);
  return data;
}

export async function loadAnnotations(bookNum: number): Promise<AnnotationBook> {
  if (annCache.has(bookNum)) return annCache.get(bookNum)!;
  const fname = `book-${String(bookNum).padStart(2, "0")}.json`;
  const res = await fetch(`/annotations/${fname}`);
  const data: AnnotationBook = res.ok
    ? await res.json()
    : { book: bookNum, annotations: [] };
  annCache.set(bookNum, data);
  return data;
}

export async function loadPath(): Promise<PathData | null> {
  const res = await fetch("/faithful/path.json");
  if (!res.ok) return null;
  return res.json();
}
