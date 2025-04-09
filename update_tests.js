const fs = require('fs');
const path = require('path');

// List of test files to update
const testFiles = [
  'frontend/src/components/clients/ClientsList.test.tsx',
  'frontend/src/components/contents/ContentForm.test.tsx',
  'frontend/src/components/contents/ContentView.test.tsx',
  'frontend/src/components/strategies/StrategyForm.test.tsx',
  'frontend/src/components/strategies/StrategyView.test.tsx',
  'frontend/src/pages/LoginPage.test.tsx'
];

// Function to update a test file
function updateTestFile(filePath) {
  console.log(`Updating ${filePath}...`);
  
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Add vitest imports if not already present
    if (!content.includes('import { describe, test, expect, beforeEach, vi } from \'vitest\';')) {
      content = content.replace(
        /import React from 'react';/,
        'import React from \'react\';\nimport { describe, test, expect, beforeEach, vi } from \'vitest\';'
      );
    }
    
    // Replace Jest mocks with Vitest mocks
    content = content.replace(/jest\.mock/g, 'vi.mock');
    content = content.replace(/jest\.fn/g, 'vi.fn');
    content = content.replace(/jest\.spyOn/g, 'vi.spyOn');
    content = content.replace(/jest\.clearAllMocks/g, 'vi.clearAllMocks');
    content = content.replace(/jest\.resetAllMocks/g, 'vi.resetAllMocks');
    content = content.replace(/jest\.restoreAllMocks/g, 'vi.restoreAllMocks');
    
    // Replace Jest mock implementations
    content = content.replace(/jest\.requireActual/g, 'vi.importActual');
    
    // Replace Jest mock types
    content = content.replace(/jest\.Mock/g, 'ReturnType<typeof vi.fn>');
    
    // Write the updated content back to the file
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Successfully updated ${filePath}`);
  } catch (error) {
    console.error(`Error updating ${filePath}:`, error);
  }
}

// Update all test files
testFiles.forEach(updateTestFile);
console.log('All test files updated successfully!');
