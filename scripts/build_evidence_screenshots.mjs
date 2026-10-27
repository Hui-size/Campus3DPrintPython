import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const runtimeRequire = createRequire(
  "C:/Users/du/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/__runtime__.cjs",
);
const { chromium } = runtimeRequire("playwright");

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = path.join(root, "results", "equivalence", "evidence_manifest.json");
const outputDir = path.join(root, "results", "equivalence", "screenshots");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
await fs.mkdir(outputDir, { recursive: true });

const records = [
  ...manifest.formal_cases.map((item) => ({
    ...item,
    methodLabel: item.method_name,
    moduleLabel: item.module_name,
    groupLabel: "正式等价类用例",
  })),
  ...manifest.supplementary_cases.map((item) => ({
    ...item,
    methodLabel: item.group,
    moduleLabel: item.group === "输入格式" ? "输入校验" : "跨模块流程",
    groupLabel: "补充检查",
    covers: "",
  })),
];

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const cardHtml = (item, index) => `
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; }
    body {
      font-family: "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif;
      color: #18212b;
      background: #edf1f4;
      padding: 28px;
    }
    .window {
      width: 1224px;
      height: 664px;
      background: #ffffff;
      border: 1px solid #d8dee4;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 18px 46px rgba(26, 39, 51, 0.12);
      display: flex;
      flex-direction: column;
    }
    .topbar {
      height: 54px;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 22px;
      background: #1f2933;
      color: #fff;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: #73808c; }
    .dot.red { background: #ef6a5b; }
    .dot.amber { background: #e9b949; }
    .dot.green { background: #59b37c; }
    .command {
      margin-left: 10px;
      font-family: Consolas, "SFMono-Regular", monospace;
      font-size: 15px;
      color: #d9e2ea;
    }
    .content { padding: 26px 30px 28px; display: flex; flex-direction: column; gap: 18px; }
    .header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
    .eyebrow { font-size: 14px; color: #61707e; margin-bottom: 7px; }
    h1 { margin: 0; font-size: 30px; line-height: 1.2; letter-spacing: 0.2px; }
    .meta { margin-top: 8px; font-size: 15px; color: #4c5b68; }
    .status {
      min-width: 106px;
      padding: 10px 15px;
      border-radius: 9px;
      background: ${item.status === "PASS" ? "#e4f4e9" : "#fde8e6"};
      color: ${item.status === "PASS" ? "#17683a" : "#a72920"};
      font-size: 22px;
      font-weight: 700;
      text-align: center;
    }
    .grid {
      display: grid;
      grid-template-columns: 190px 1fr;
      border: 1px solid #d9e0e5;
      border-radius: 11px;
      overflow: hidden;
      font-size: 16px;
      line-height: 1.55;
    }
    .label, .value { min-height: 58px; padding: 14px 18px; border-bottom: 1px solid #e4e9ed; }
    .label { background: #f4f7f9; color: #52616e; font-weight: 600; }
    .value { background: #fff; overflow-wrap: anywhere; }
    .grid > :nth-last-child(-n+2) { border-bottom: 0; }
    code {
      font-family: Consolas, "SFMono-Regular", monospace;
      font-size: 15px;
      background: #f2f5f7;
      border-radius: 5px;
      padding: 2px 6px;
    }
    .footer {
      margin-top: auto;
      display: flex;
      justify-content: space-between;
      color: #70808d;
      font-size: 13px;
      padding-top: 4px;
    }
  </style>
</head>
<body>
  <div class="window">
    <div class="topbar">
      <span class="dot red"></span><span class="dot amber"></span><span class="dot green"></span>
      <span class="command">python equivalence_test_runner.py</span>
    </div>
    <div class="content">
      <div class="header">
        <div>
          <div class="eyebrow">${escapeHtml(item.groupLabel)} · ${index}/${records.length}</div>
          <h1>${escapeHtml(item.id)}　${escapeHtml(item.description)}</h1>
          <div class="meta">${escapeHtml(item.methodLabel)}　|　${escapeHtml(item.moduleLabel)}</div>
        </div>
        <div class="status">${escapeHtml(item.status)}</div>
      </div>
      <div class="grid">
        <div class="label">测试输入</div>
        <div class="value"><code>${escapeHtml(item.inputs)}</code></div>
        <div class="label">预期结果</div>
        <div class="value"><code>${escapeHtml(item.expected)}</code></div>
        <div class="label">实际结果</div>
        <div class="value"><code>${escapeHtml(item.actual)}</code></div>
        <div class="label">覆盖等价类</div>
        <div class="value">${escapeHtml(item.covers || "补充检查，不单独计入等价类覆盖数量")}</div>
      </div>
      <div class="footer">
        <span>校园 3D 打印服务系统 · 实验二等价类测试</span>
        <span>${escapeHtml(manifest.executed_at)} · Python ${escapeHtml(manifest.python)}</span>
      </div>
    </div>
  </div>
</body>
</html>`;

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
});
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });

for (let index = 0; index < records.length; index += 1) {
  const item = records[index];
  await page.setContent(cardHtml(item, index + 1), { waitUntil: "load" });
  await page.screenshot({
    path: path.join(outputDir, `${item.id}.png`),
    type: "png",
    fullPage: false,
  });
}

await browser.close();
console.log(JSON.stringify({ outputDir, count: records.length }, null, 2));
