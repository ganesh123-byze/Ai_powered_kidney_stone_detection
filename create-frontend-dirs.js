const fs = require('fs');
const path = require('path');

const baseDir = 'd:\\Kidney Detection\\frontend\\src';
const dirs = [
  'api',
  'components',
  'pages',
  'types'
];

try {
  dirs.forEach(dir => {
    const fullPath = path.join(baseDir, dir);
    fs.mkdirSync(fullPath, { recursive: true });
    console.log(`✓ Created: ${fullPath}`);
  });
  console.log('\n✓ All directories created successfully');
} catch (err) {
  console.error('Error creating directories:', err.message);
  process.exit(1);
}
