// Script to fix import paths in Next.js files
const fs = require('fs');
const path = require('path');

// Function to recursively find all .tsx and .ts files
function findFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      findFiles(filePath, fileList);
    } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

// Function to fix imports in a file
function fixImports(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace @/ imports with relative paths
  content = content.replace(/from\s+["']@\/([^"']+)["']/g, (match, importPath) => {
    return `from "./${importPath}"`;
  });
  
  fs.writeFileSync(filePath, content);
  console.log(`Fixed imports in ${filePath}`);
}

// Main function
function main() {
  const frontendDir = path.join(__dirname, 'Frontend');
  const files = findFiles(frontendDir);
  
  files.forEach(file => {
    fixImports(file);
  });
  
  console.log(`Fixed imports in ${files.length} files`);
}

main();
