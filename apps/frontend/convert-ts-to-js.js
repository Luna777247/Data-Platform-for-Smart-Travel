import { Project } from "ts-morph";
import fs from "fs";
import path from "path";

// Default source directory for UI components. Set the SRC_DIR env var to override.
const SRC_DIR = process.env.SRC_DIR || "./components/ui"; // was ./app/components/ui

// Tạo dự án TS-morph
const project = new Project({
  skipAddingFilesFromTsConfig: true,
});

// Hàm chuyển đổi 1 file
function convertFile(filePath) {
  const sourceFile = project.addSourceFileAtPath(filePath);

  // Xóa type và interface
  sourceFile.getInterfaces().forEach(i => i.remove());
  sourceFile.getTypeAliases().forEach(t => t.remove());

  // Xóa type annotation và generic
  sourceFile.forEachDescendant(node => {
    if (node.getKindName() === "TypeAssertionExpression") node.replaceWithText(node.getExpression().getText());
    if (node.getKindName() === "AsExpression") node.replaceWithText(node.getExpression().getText());
  });

  // Xuất nội dung JavaScript (xóa type)
  const jsCode = sourceFile.getFullText()
    .replace(/:\s*[\w<>{}\[\]|?]+/g, "") // loại bỏ kiểu dữ liệu đơn giản
    .replace(/import\s+type\s+/g, "import ") // sửa import type
    .replace(/}\s*\.\s*ComponentProps\s*<[^>]+>\s*&?\s*VariantProps\s*<[^>]+>\s*&?\s*\{[^}]*\}\s*\)?/g, "}") // remove ComponentProps and VariantProps
    .replace(/}\s*\.\s*ComponentProps\s*<[^>]+>\s*\)?/g, "}") // remove ComponentProps

  const newFilePath = filePath
    .replace(".tsx", ".jsx")
    .replace(".ts", ".js");

  fs.writeFileSync(newFilePath, jsCode, "utf8");
  console.log(`✅ Converted: ${path.basename(filePath)} → ${path.basename(newFilePath)}`);
  // fs.unlinkSync(filePath); // commented out to keep original
}

// Traverse all directories
function walkDir(dir) {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) walkDir(filePath);
    else if (file.endsWith(".tsx") || file.endsWith(".ts") || file.endsWith(".jsx")) convertFile(filePath);
  });
}

walkDir(SRC_DIR);
console.log("🎉 All TypeScript files converted to JavaScript!");
