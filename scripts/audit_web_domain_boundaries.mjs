import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const legacyClient = resolve(root, "apps/web/src/services/safehomeApi.ts");
const domainFacade = resolve(root, "apps/web/src/services/domainApi.ts");
const maxLegacyClientLines = 2700;

const violations = [];
const warnings = [];

const legacyText = readFileSync(legacyClient, "utf8");
const legacyLines = legacyText.split(/\r?\n/).length;
if (legacyLines > maxLegacyClientLines) {
  violations.push({
    rule: "freeze_legacy_god_client_growth",
    path: "apps/web/src/services/safehomeApi.ts",
    line_count: legacyLines,
    max_lines: maxLegacyClientLines,
    message: "旧 safehomeApi.ts 已超过冻结阈值；新增能力应进入分域 client，而不是继续扩大 God Client。",
  });
}

const domainText = readFileSync(domainFacade, "utf8");
for (const required of ["participantApi", "researchApi", "governanceApi", "internalRdApi"]) {
  if (!domainText.includes(`export const ${required}`)) {
    violations.push({
      rule: "domain_facade_required",
      path: "apps/web/src/services/domainApi.ts",
      message: `缺少 ${required} 分域入口。`,
    });
  }
}

function addedSourceFiles() {
  const base = process.env.GITHUB_BASE_REF?.trim();
  if (!base) return [];
  try {
    const output = execFileSync(
      "git",
      ["diff", "--diff-filter=A", "--name-only", `origin/${base}...HEAD`],
      { cwd: root, encoding: "utf8" },
    );
    return output
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter((item) => /^apps\/web\/src\/.*\.(?:ts|tsx)$/.test(item));
  } catch (error) {
    warnings.push({
      rule: "new_file_diff_unavailable",
      message: "无法读取 base diff；本地运行时仅执行静态边界检查。",
    });
    return [];
  }
}

for (const path of addedSourceFiles()) {
  if (path === "apps/web/src/services/domainApi.ts") continue;
  const text = readFileSync(resolve(root, path), "utf8");
  if (/from\s+["'][^"']*services\/safehomeApi["']/.test(text)) {
    violations.push({
      rule: "new_web_code_must_use_domain_api",
      path,
      message: "新 Web 源文件不得直接依赖 safehomeApi；请从 services/domainApi 导入对应领域 facade。",
    });
  }
}

const result = {
  ok: violations.length === 0,
  architecture: "incremental_domain_facade",
  legacy_client_line_count: legacyLines,
  legacy_client_max_lines: maxLegacyClientLines,
  violations,
  warnings,
};
console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
