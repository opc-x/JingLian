/** 教材原文层 — 只读 */
export interface VerbatimLine {
  text: string;
  encrypted?: boolean;
}

export interface FaithfulPage {
  pageNum: number;
  image: string;
  lineCount: number;
  lines: VerbatimLine[];
}

export interface FaithfulLesson {
  lessonId: number;
  title: string;
  pageCount: number;
  pages: FaithfulPage[];
}

export interface FaithfulBook {
  book: number;
  mode: "faithful";
  policy: string;
  title: string;
  cefr: string;
  lessonCount: number;
  lessons: FaithfulLesson[];
}

export interface VolumeIndex {
  book: number;
  title: string;
  file: string;
  annotationFile: string;
  lessonCount: number;
  pageCount?: number;
  coverImage?: string;
  cefr?: string;
}

/** 一级类目 */
export interface CategoryIndex {
  id: string;
  title: string;
  subtitle?: string;
  cefr?: string;
  bookCount: number;
  lessonCount: number;
  pageCount?: number;
  books: VolumeIndex[];
}

export interface FaithfulCatalog {
  mode: "faithful";
  categories: CategoryIndex[];
  /** @deprecated 兼容旧 index */
  series?: CategoryIndex[];
}

export interface VocabItem {
  word: string;
  ipa: string;
  pos?: string;
  zh: string;
  /** 本页哪句问答在练这个词 */
  inDrill?: string;
  note?: string;
  audio?: string;
}

export interface PatternItem {
  en: string;
  zh: string;
  /** 为什么用这种句型 */
  why: string;
  /** 什么时候用 */
  when: string;
  /** 怎么问、怎么答（含 Callan 节奏） */
  how: string;
  /** 教材本页对练例句 */
  drills?: string[];
  /** 离开课堂后的真实场景 */
  realLife?: string;
  /** @deprecated 旧批注兼容 */
  examples?: string[];
}

export interface GrammarItem {
  title: string;
  body: string;
}

export interface UsageItem {
  title: string;
  body: string;
}

export interface AnnotationBlocks {
  vocab?: VocabItem[];
  patterns?: PatternItem[];
  grammar?: GrammarItem[];
  usage?: UsageItem[];
}

export interface PageAnnotation {
  lessonId: number;
  pageNum: number;
  summaryZh?: string;
  chartRef?: number | null;
  blocks?: AnnotationBlocks;
  generatedAt?: string;
  model?: string;
  /** @deprecated */
  notes?: string[];
  hints?: string[];
}

export interface AnnotationBook {
  book: number;
  annotations: PageAnnotation[];
}

export interface CefrLevel {
  cefr: string;
  label: string;
  books: number[];
  lessonRange: { from: number; to: number };
  skills: string[];
  canDo: string[];
}

export interface PathNode {
  book: number;
  lessonId: number;
  title: string;
  cefr: string;
  blocks: number;
  vocabulary: number;
  drills: number;
}

export interface PathData {
  title: string;
  updatedAt: string;
  totalLessons: number;
  cefrLevels: CefrLevel[];
  nodes: PathNode[];
}
