#!/usr/bin/env node
import fs from 'fs'
import path from 'path'

const UI_DIR = path.resolve(process.cwd(), 'components', 'ui')

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
}

function createShim(jsPath, jsxRelPath) {
  if (fs.existsSync(jsPath)) return false
  const content = `export { default } from '${jsxRelPath}'\nexport * from '${jsxRelPath}'\n`
  fs.writeFileSync(jsPath, content, 'utf8')
  return true
}

function run() {
  if (!fs.existsSync(UI_DIR)) {
    console.error('UI directory not found:', UI_DIR)
    process.exitCode = 2
    return
  }

  const files = fs.readdirSync(UI_DIR)
  let created = 0
  files.forEach(f => {
    const full = path.join(UI_DIR, f)
    const stat = fs.statSync(full)
    if (stat.isFile() && f.endsWith('.jsx')) {
      const basename = f.replace(/\.jsx$/, '')
      const jsName = basename + '.js'
      const jsPath = path.join(UI_DIR, jsName)
      const jsxRel = `./${basename}.jsx`
      if (createShim(jsPath, jsxRel)) created++
    }
  })

  console.log(`Created ${created} shim(s) in ${UI_DIR}`)
}

run()
