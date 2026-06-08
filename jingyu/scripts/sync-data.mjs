import { cpSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

function copyJsonDir(src, dest) {
  if (!existsSync(src)) return;
  mkdirSync(dest, { recursive: true });
  for (const name of readdirSync(src).filter((n) => n.endsWith(".json"))) {
    cpSync(join(src, name), join(dest, name));
  }
}

function copyTree(src, dest) {
  if (!existsSync(src)) return;
  mkdirSync(dest, { recursive: true });
  for (const name of readdirSync(src)) {
    const from = join(src, name);
    const to = join(dest, name);
    cpSync(from, to, { recursive: true });
  }
}

// 教材原文（faithful）
const faithfulSrc = join(root, "sources/callan/faithful");
const publicRoot = join(root, "jingyu/public");
copyJsonDir(faithfulSrc, join(publicRoot, "faithful"));

// 页图
copyTree(join(root, "sources/callan/pages"), join(publicRoot, "pages"));

// 批注层（与原文分离）
copyJsonDir(join(root, "annotations/callan"), join(publicRoot, "annotations"));

// 发音 MP3（generate_audio.py 写入 jingyu/public/audio，已在 public 内）

// CEFR 参考
const cefrSrc = join(root, "data/callan/cefr.json");
if (existsSync(cefrSrc)) {
  mkdirSync(join(publicRoot, "faithful"), { recursive: true });
  cpSync(cefrSrc, join(publicRoot, "faithful/cefr.json"));
}

// 兼容路径页
const pathSrc = join(root, "distilled/callan/path.json");
if (existsSync(pathSrc)) {
  cpSync(pathSrc, join(publicRoot, "faithful/path.json"));
}

console.log("[sync-data] faithful + pages + annotations → jingyu/public/");
