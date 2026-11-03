#!/usr/bin/env node
/** Parse every published TeX expression with the same local KaTeX as readers. */
const fs = require('node:fs');
const path = require('node:path');
const katex = require('./vendor/katex/katex.js');
const root = path.resolve(__dirname, '..');
const errors = [];
let expressions = 0;
function decode(text) {
  return text.replace(/&#(x[\da-f]+|\d+);/gi, (_, n) => String.fromCodePoint(
    n[0].toLowerCase() === 'x' ? parseInt(n.slice(1), 16) : Number(n)))
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'").replace(/&amp;/g, '&');
}
for (const paper of fs.readdirSync(path.join(root, 'content'))) {
  const directory = path.join(root, 'content', paper);
  if (!fs.statSync(directory).isDirectory()) continue;
  for (const file of fs.readdirSync(directory).filter(file => file.endsWith('.html'))) {
    const html = fs.readFileSync(path.join(directory, file), 'utf8');
    const text = decode(html);
    const starts = [...text.matchAll(/\\\(|\\\[/g)].length;
    const ends = [...text.matchAll(/\\\)|\\\]/g)].length;
    if (starts !== ends) errors.push({paper, file, error: 'Unbalanced math delimiters'});
    for (const match of text.matchAll(/\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]/g)) {
      const tex = match[1] ?? match[2];
      expressions++;
      try {
        if (!tex.trim()) throw new Error('Empty formula');
        katex.renderToString(tex, {throwOnError: true, strict: 'ignore', trust: false, displayMode: match[2] !== undefined});
      } catch (error) {
        errors.push({paper, file, tex, error: error.message});
      }
    }
    if (html.includes('行内公式见原版')) errors.push({paper, file, error: 'Unrepaired inline math placeholder'});
  }
}
console.log(JSON.stringify({expressions, errors}, null, 2));
process.exitCode = errors.length ? 1 : 0;
