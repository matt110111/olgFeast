import tsParser from '@typescript-eslint/parser';
export default [{
  files: ['src/**/*.{ts,tsx}'],
  languageOptions: { parser: tsParser, parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } } },
  rules: { 'no-debugger': 'error', 'no-dupe-keys': 'error', 'no-unreachable': 'error', 'no-constant-condition': ['error', { checkLoops: false }] },
}];
