const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '.next/standalone/server.js');
if (fs.existsSync(filePath)) {
  let content = fs.readFileSync(filePath, 'utf8');
  const target = "require('next')";
  
  const replacement = `require('next')

// ============= PATCH: Radix Tooltip Context Fix =============
const moduleAlias = require('module');
const originalRequire = moduleAlias.prototype.require;
moduleAlias.prototype.require = function(...args) {
  const name = args[0];
  const exported = originalRequire.apply(this, args);
  if (name === '@radix-ui/react-tooltip') {
    if (!exported.__isMocked) {
      exported.__isMocked = true;
      try {
        const React = require('react');
        const OriginalRoot = exported.Root || exported.Tooltip;
        const TooltipProvider = exported.Provider || exported.TooltipProvider;
        if (OriginalRoot && TooltipProvider) {
          const MockedRoot = function(props) {
            return React.createElement(TooltipProvider, {}, React.createElement(OriginalRoot, props));
          };
          Object.assign(MockedRoot, OriginalRoot);
          exported.Root = MockedRoot;
          exported.Tooltip = MockedRoot;
        }
      } catch (err) {}
    }
  }
  return exported;
};
`;

  if (content.includes(target) && !content.includes('@radix-ui/react-tooltip')) {
    content = content.replace(target, replacement);
    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Successfully patched standalone server.js!');
  } else {
    console.log('standalone server.js already patched or target not found.');
  }
} else {
  console.log('standalone server.js not found at: ' + filePath);
}
