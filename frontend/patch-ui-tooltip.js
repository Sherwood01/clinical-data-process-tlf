const fs = require('fs');
const path = require('path');

// =====================================================================
// 修补 @hexclave/ui 的 SimpleTooltip，让它自包含 TooltipProvider
// 这样无论 React Context 是否有多实例，SimpleTooltip 都能独立工作
// =====================================================================

function patchSimpleTooltip(filePath, isESM) {
  if (!fs.existsSync(filePath)) {
    console.log('File not found, skipping:', filePath);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  if (content.includes('__PATCHED_WITH_PROVIDER__')) {
    console.log('Already patched:', filePath);
    return;
  }

  if (isESM) {
    // ESM 版本：在 import 列表加入 TooltipProvider，并包裹 Tooltip
    content = content.replace(
      'import { Tooltip, TooltipContent, TooltipTrigger, cn } from "../index.js";',
      'import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider, cn } from "../index.js"; // __PATCHED_WITH_PROVIDER__'
    );
    // 把 return jsxs(Tooltip, ... 改成 return jsx(TooltipProvider, { children: jsxs(Tooltip, ...
    // 原始代码末尾是 }); 我们需要包裹一层
    content = content.replace(
      /return \/\* @__PURE__ \*\/ jsxs\(Tooltip,/,
      'return /* @__PURE__ */ jsx(TooltipProvider, { children: /* @__PURE__ */ jsxs(Tooltip,'
    );
    // 在最后一个 }); 前加上 }); 来关闭 TooltipProvider
    // 找到 SimpleTooltip 函数结尾：最后的 }); 后跟换行和 }
    content = content.replace(
      /(\]\s*\}\s*\)\s*;\s*\n\}\n\n\/\/#endregion)/,
      ']  })}); \n}\n\n//#endregion'
    );
  } else {
    // CJS 版本
    content = content.replace(
      'let ___index_js = require("../index.js");',
      'let ___index_js = require("../index.js"); // __PATCHED_WITH_PROVIDER__'
    );
    content = content.replace(
      /return \/\* @__PURE__ \*\/ \(0, react_jsx_runtime\.jsxs\)\(___index_js\.Tooltip,/,
      'return /* @__PURE__ */ (0, react_jsx_runtime.jsx)(___index_js.TooltipProvider, { children: /* @__PURE__ */ (0, react_jsx_runtime.jsxs)(___index_js.Tooltip,'
    );
    content = content.replace(
      /(\]\s*\}\s*\)\s*;\s*\n\}\n\n\/\/#endregion)/,
      ']  })}); \n}\n\n//#endregion'
    );
  }

  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully patched:', filePath);
}

patchSimpleTooltip(
  path.join(__dirname, 'node_modules/@hexclave/ui/dist/esm/components/simple-tooltip.js'),
  true
);
patchSimpleTooltip(
  path.join(__dirname, 'node_modules/@hexclave/ui/dist/components/simple-tooltip.js'),
  false
);

console.log('Done patching SimpleTooltip!');
