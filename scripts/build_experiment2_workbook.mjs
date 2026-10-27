import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = path.join(root, "results", "equivalence", "evidence_manifest.json");
const outputDir = path.join(root, "实验二");
const previewDir = path.join(root, ".experiment2_build", "previews");
const outputPath = path.join(outputDir, "实验二_等价类测试用例.xlsx");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const font = "Microsoft YaHei";
const navy = "#17324D";
const blue = "#2F6B8A";
const paleBlue = "#EAF2F7";
const paleGray = "#F5F7F9";
const border = "#D9E0E5";
const darkText = "#1E2933";

const workbook = Workbook.create();

function setTitle(sheet, range, text, subtitle = "") {
  sheet.getRange(range).values = [[text]];
  sheet.getRange(range).format.font = { name: font, size: 16, bold: true, color: "#000000" };
  sheet.getRange(range).format.verticalAlignment = "center";
  sheet.getRange(range).format.rowHeight = 28;
  if (subtitle) {
    sheet.getRange(range.replace(/\d+$/, (n) => String(Number(n) + 1))).values = [[subtitle]];
  }
}

function styleHeader(range) {
  range.format = {
    fill: navy,
    font: { name: font, size: 10, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
  };
  range.format.rowHeight = 27;
  range.format.borders = { preset: "all", style: "thin", color: "#FFFFFF" };
}

function styleTableBody(range) {
  range.format = {
    font: { name: font, size: 10, color: darkText },
    verticalAlignment: "center",
    wrapText: true,
  };
  range.format.borders = { preset: "all", style: "thin", color: border };
}

// Summary
const summary = workbook.worksheets.add("摘要");
summary.tabColor = navy;
summary.showGridLines = false;
setTitle(
  summary,
  "A2",
  "实验二等价类测试结果",
  "校园 3D 打印服务系统  |  测试执行结果与覆盖汇总",
);
summary.getRange("A4:F4").merge();
summary.getRange("A4:F4").values = [[
  "本工作簿汇总 57 个等价类、58 条正式等价类用例和 15 条补充检查；所有执行项均与预期结果一致。",
]];
summary.getRange("A4:F4").format = {
  font: { name: font, size: 10, color: "#52616E" },
  wrapText: true,
  verticalAlignment: "center",
};
summary.getRange("A4:F4").format.rowHeight = 30;

summary.getRange("A6:E6").values = [[
  "测试方法", "用例数", "通过", "失败", "特点",
]];
styleHeader(summary.getRange("A6:E6"));
summary.getRange("A7:E9").values = [
  ["弱一般等价类", null, null, null, "覆盖全部有效类，使用最少正常用例"],
  ["强一般等价类", null, null, null, "覆盖全部正常输入组合，检查变量交互"],
  ["弱健壮等价类", null, null, null, "增加单个无效输入，覆盖全部无效类"],
];
summary.getRange("B7:B9").formulas = [
  ["=COUNTIF('测试用例'!$C$6:$C$78,\"弱一般等价类\")"],
  ["=COUNTIF('测试用例'!$C$6:$C$78,\"强一般等价类\")"],
  ["=COUNTIF('测试用例'!$C$6:$C$78,\"弱健壮等价类\")"],
];
summary.getRange("C7:C9").formulas = [
  ["=COUNTIFS('测试用例'!$C$6:$C$78,\"弱一般等价类\",'测试用例'!$I$6:$I$78,\"PASS\")"],
  ["=COUNTIFS('测试用例'!$C$6:$C$78,\"强一般等价类\",'测试用例'!$I$6:$I$78,\"PASS\")"],
  ["=COUNTIFS('测试用例'!$C$6:$C$78,\"弱健壮等价类\",'测试用例'!$I$6:$I$78,\"PASS\")"],
];
summary.getRange("D7:D9").formulas = [["=B7-C7"], ["=B8-C8"], ["=B9-C9"]];
summary.getRange("A10:E10").values = [["合计", null, null, null, "正式等价类用例"]];
summary.getRange("B10:D10").formulas = [["=SUM(B7:B9)", "=SUM(C7:C9)", "=SUM(D7:D9)"]];
styleTableBody(summary.getRange("A7:E9"));
styleTableBody(summary.getRange("A10:E10"));
summary.getRange("A10:E10").format.fill = paleBlue;
summary.getRange("A10:E10").format.font = { name: font, size: 10, bold: true, color: darkText };
summary.getRange("B7:D10").format.horizontalAlignment = "center";

summary.getRange("A12:B12").values = [["总体结果", "数值"]];
styleHeader(summary.getRange("A12:B12"));
summary.getRange("A13:B18").values = [
  ["等价类数量", null],
  ["补充检查数量", null],
  ["总执行项", null],
  ["通过", null],
  ["失败", null],
  ["缺陷状态", "未发现程序缺陷"],
];
summary.getRange("B13").formulas = [["=COUNTA('等价类'!A6:A62)"]];
summary.getRange("B14").formulas = [["=COUNTIF('测试用例'!$B$6:$B$78,\"补充检查\")"]];
summary.getRange("B15").formulas = [["=B10+B14"]];
summary.getRange("B16").formulas = [[
  "=C10+COUNTIFS('测试用例'!$B$6:$B$78,\"补充检查\",'测试用例'!$I$6:$I$78,\"PASS\")",
]];
summary.getRange("B17").formulas = [["=B15-B16"]];
styleTableBody(summary.getRange("A13:B18"));
summary.getRange("B13:B18").format.horizontalAlignment = "center";
summary.getRange("A13:B18").format.rowHeight = 24;
summary.getRange("A18:B18").format.rowHeight = 36;

summary.getRange("D13:F18").merge();
summary.getRange("D13:F18").values = [[
  "方法比较结论\n弱一般用例最少，只验证正常等价类。强一般用例覆盖正常输入组合，能发现变量交互问题。"
  + "弱健壮增加每个无效等价类的单缺陷用例，覆盖面最大，是本实验发现异常处理问题的主要手段。",
]];
summary.getRange("D13:F18").format = {
  fill: paleGray,
  font: { name: font, size: 10, color: darkText },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "all", style: "thin", color: border },
};

summary.getRange("A20:F20").merge();
summary.getRange("A20:F20").values = [[
  `数据来源：equivalence_test_runner.py 自动执行结果，运行时间 ${manifest.executed_at}，Python ${manifest.python}。`,
]];
summary.getRange("A20:F20").format = {
  font: { name: font, size: 9, italic: true, color: "#61707E" },
  wrapText: true,
};

for (const [column, width] of Object.entries({
  A: 22, B: 18, C: 12, D: 12, E: 42, F: 14,
})) {
  summary.getRange(`${column}1:${column}20`).format.columnWidth = width;
}

// Equivalence classes
const classes = workbook.worksheets.add("等价类");
classes.tabColor = blue;
classes.showGridLines = false;
setTitle(
  classes,
  "A2",
  "等价类划分与覆盖矩阵",
  "每个等价类使用唯一编号；正式用例按三种方法分别覆盖，弱健壮方法覆盖全部有效类和无效类。",
);
classes.getRange("A5:I5").values = [[
  "编号", "模块", "变量", "类型", "划分规则", "代表值",
  "弱一般", "强一般", "弱健壮",
]];
styleHeader(classes.getRange("A5:I5"));

const classRows = manifest.classes.map((item) => [
  item.id,
  item.module_name,
  item.variable,
  item.kind,
  item.rule,
  Number(item.representative),
  item.covered_by.includes("weak_general") ? "✓" : "",
  item.covered_by.includes("strong_general") ? "✓" : "",
  item.covered_by.includes("weak_robust") ? "✓" : "",
]);
classes.getRange(`A6:I${5 + classRows.length}`).values = classRows;
styleTableBody(classes.getRange(`A6:I${5 + classRows.length}`));
classes.getRange(`A6:A${5 + classRows.length}`).format.horizontalAlignment = "center";
classes.getRange(`B6:D${5 + classRows.length}`).format.horizontalAlignment = "center";
classes.getRange(`F9:I${5 + classRows.length}`).format.horizontalAlignment = "center";
classes.getRange(`G6:I${5 + classRows.length}`).format.font = {
  name: font, size: 10, bold: true, color: "#17683A",
};
classes.getRange(`A5:I${5 + classRows.length}`).format.borders = {
  preset: "all", style: "thin", color: border,
};
classes.getRange(`A5:I${5 + classRows.length}`).format.wrapText = true;
classes.getRange(`A5:I${5 + classRows.length}`).format.verticalAlignment = "center";
classes.getRange(`A6:I${5 + classRows.length}`).format.autofitRows();
for (const [column, width] of Object.entries({
  A: 13, B: 16, C: 12, D: 9, E: 28, F: 10, G: 10, H: 10, I: 10,
})) {
  classes.getRange(`${column}1:${column}${5 + classRows.length}`).format.columnWidth = width;
}
classes.freezePanes.freezeRows(5);

const classTable = classes.tables.add(
  `A5:I${5 + classRows.length}`,
  true,
  "EquivalenceClasses",
);
classTable.style = "TableStyleMedium2";
classTable.showFilterButton = true;

// Test cases
const cases = workbook.worksheets.add("测试用例");
cases.tabColor = "#5D8AA8";
cases.showGridLines = false;
setTitle(
  cases,
  "A2",
  "等价类测试用例与执行结果",
  "正式用例、输入格式检查和跨模块流程检查共用一张可筛选表；实际结果由被测系统执行产生。",
);
cases.getRange("A5:J5").values = [[
  "编号", "类别", "测试方法", "模块", "说明", "输入",
  "预期结果", "实际结果", "状态", "覆盖等价类",
]];
styleHeader(cases.getRange("A5:J5"));

const formalRows = manifest.formal_cases.map((item) => [
  item.id,
  "正式等价类用例",
  item.method_name,
  item.module_name,
  item.description,
  item.inputs,
  item.expected,
  item.actual,
  item.status,
  item.covers,
]);
const supplementaryRows = manifest.supplementary_cases.map((item) => [
  item.id,
  "补充检查",
  item.group,
  item.group === "输入格式" ? "输入校验" : "跨模块流程",
  item.description,
  item.inputs,
  item.expected,
  item.actual,
  item.status,
  "",
]);
const caseRows = [...formalRows, ...supplementaryRows];
cases.getRange(`A6:J${5 + caseRows.length}`).values = caseRows;
styleTableBody(cases.getRange(`A6:J${5 + caseRows.length}`));
cases.getRange(`A6:D${5 + caseRows.length}`).format.horizontalAlignment = "center";
cases.getRange(`I6:I${5 + caseRows.length}`).format.horizontalAlignment = "center";
cases.getRange(`F6:H${5 + caseRows.length}`).format.font = {
  name: "Consolas", size: 9, color: darkText,
};
cases.getRange(`A5:J${5 + caseRows.length}`).format.borders = {
  preset: "all", style: "thin", color: border,
};
cases.getRange(`A5:J${5 + caseRows.length}`).format.wrapText = true;
cases.getRange(`A5:J${5 + caseRows.length}`).format.verticalAlignment = "center";
cases.getRange(`A6:J${5 + caseRows.length}`).format.autofitRows();
for (const [column, width] of Object.entries({
  A: 12, B: 18, C: 18, D: 14, E: 26, F: 30, G: 43, H: 43, I: 9, J: 35,
})) {
  cases.getRange(`${column}1:${column}${5 + caseRows.length}`).format.columnWidth = width;
}
cases.freezePanes.freezeRows(5);
cases.freezePanes.freezeColumns(1);

const caseTable = cases.tables.add(
  `A5:J${5 + caseRows.length}`,
  true,
  "TestCases",
);
caseTable.style = "TableStyleMedium2";
caseTable.showFilterButton = true;

cases.getRange(`I6:I${5 + caseRows.length}`).conditionalFormats.add("cellIs", {
  operator: "equal",
  formula: "\"FAIL\"",
  format: {
    fill: "#F4CCCC",
    font: { bold: true, color: "#9C0006" },
  },
});

// Evidence index
const evidence = workbook.worksheets.add("证据索引");
evidence.tabColor = "#8CA6B7";
evidence.showGridLines = false;
setTitle(
  evidence,
  "A2",
  "逐用例执行证据索引",
  "每条记录对应 results/equivalence/screenshots 目录中的同名 PNG 文件。",
);
evidence.getRange("A4:E4").values = [[
  "用例编号", "类别", "结果", "截图文件", "被测功能",
]];
styleHeader(evidence.getRange("A4:E4"));
const evidenceRows = [
  ...manifest.formal_cases.map((item) => [
    item.id, item.method_name, item.status, `${item.id}.png`, item.module_name,
  ]),
  ...manifest.supplementary_cases.map((item) => [
    item.id, item.group, item.status, `${item.id}.png`,
    item.group === "输入格式" ? "输入校验" : "跨模块流程",
  ]),
];
evidence.getRange(`A5:E${4 + evidenceRows.length}`).values = evidenceRows;
styleTableBody(evidence.getRange(`A5:E${4 + evidenceRows.length}`));
evidence.getRange(`A5:C${4 + evidenceRows.length}`).format.horizontalAlignment = "center";
evidence.getRange(`A4:E${4 + evidenceRows.length}`).format.borders = {
  preset: "all", style: "thin", color: border,
};
evidence.getRange(`A4:E${4 + evidenceRows.length}`).format.wrapText = true;
evidence.getRange(`A4:E${4 + evidenceRows.length}`).format.verticalAlignment = "center";
evidence.getRange(`A5:E${4 + evidenceRows.length}`).format.autofitRows();
for (const [column, width] of Object.entries({ A: 13, B: 20, C: 10, D: 22, E: 20 })) {
  evidence.getRange(`${column}1:${column}${4 + evidenceRows.length}`).format.columnWidth = width;
}
evidence.freezePanes.freezeRows(4);
const evidenceTable = evidence.tables.add(
  `A4:E${4 + evidenceRows.length}`,
  true,
  "EvidenceIndex",
);
evidenceTable.style = "TableStyleMedium2";
evidenceTable.showFilterButton = true;

workbook.recalculate();

const summaryCheck = await workbook.inspect({
  kind: "table",
  range: "摘要!A5:F20",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 8,
});
console.log("SUMMARY_CHECK");
console.log(summaryCheck.ndjson);

const matchCheck = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "Final formula error scan",
});
console.log("FORMULA_SCAN");
console.log(matchCheck.ndjson);

for (const sheetName of ["摘要", "等价类", "测试用例", "证据索引"]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(
    path.join(previewDir, `${sheetName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, sheets: 4, cases: caseRows.length }, null, 2));
