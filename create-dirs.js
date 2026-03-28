const fs = require('fs');
const path = require('path');

const baseDir = 'd:\\Kidney Detection\\backend';
const dirs = [
  'app/routes',
  'app/services',
  'app/models',
  'app/schemas',
  'training',
  'data/raw',
  'data/processed',
  'saved_models'
];

try {
  dirs.forEach(dir => {
    const fullPath = path.join(baseDir, dir);
    fs.mkdirSync(fullPath, { recursive: true });
    console.log(`Created: ${fullPath}`);
  });
  console.log('\n✓ All directories created successfully');
} catch (err) {
  console.error('Error creating directories:', err.message);
  process.exit(1);
}
