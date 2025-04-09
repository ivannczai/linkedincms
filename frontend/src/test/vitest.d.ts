/// <reference types="vitest" />
/// <reference types="@testing-library/jest-dom" />

// Extend the window interface to include testing globals
interface Window {
  jest: typeof import('vitest');
  test: typeof import('vitest').test;
  describe: typeof import('vitest').describe;
  expect: typeof import('vitest').expect;
  beforeEach: typeof import('vitest').beforeEach;
  afterEach: typeof import('vitest').afterEach;
  beforeAll: typeof import('vitest').beforeAll;
  afterAll: typeof import('vitest').afterAll;
}
