#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Configuration
const PUBLIC_DIR = path.join(__dirname, '..', 'public')
const RESOURCES_DIR = path.join(PUBLIC_DIR, 'resources')
const MANIFEST_FILE = path.join(PUBLIC_DIR, 'manifest.json')

// File extensions to include
const ALLOWED_EXTENSIONS = [
  // Programming
  '.py', '.pyx', '.pyi', '.rs', '.c', '.h', '.cpp', '.cc', '.cxx', '.hpp',
  '.ts', '.tsx', '.js', '.jsx', '.vue',
  // Shell
  '.sh', '.bash', '.zsh', '.fish',
  // Config
  '.toml', '.yaml', '.yml', '.json', '.jsonc', '.xml', '.ini', '.cfg', '.conf',
  // Docs
  '.md', '.mdx', '.rst', '.txt', '.pdf',
  // Data
  '.csv', '.tsv', '.data', '.perf',
  // Images
  '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp',
  // Web
  '.html', '.htm', '.css', '.scss', '.sass', '.less'
]

// Special files to include (without extension)
const SPECIAL_FILES = ['Makefile', 'makefile', 'MAKEFILE', 'Dockerfile', 'LICENSE', 'README']

/**
 * Check if a file should be included in the manifest
 */
function shouldIncludeFile(filename) {
  // Check special files
  if (SPECIAL_FILES.includes(filename)) {
    return true
  }
  
  // Check extensions
  const ext = path.extname(filename).toLowerCase()
  return ALLOWED_EXTENSIONS.includes(ext)
}

/**
 * Recursively scan directory and build file tree
 */
function scanDirectory(dir, baseDir = '') {
  const files = []
  const items = fs.readdirSync(dir, { withFileTypes: true })
  
  for (const item of items) {
    // Skip hidden files and directories
    if (item.name.startsWith('.')) continue
    
    const fullPath = path.join(dir, item.name)
    const relativePath = path.join(baseDir, item.name)
    
    if (item.isDirectory()) {
      // Recursively scan subdirectories
      const subFiles = scanDirectory(fullPath, relativePath)
      files.push(...subFiles)
    } else if (item.isFile() && shouldIncludeFile(item.name)) {
      // Add file to list with relative path from resources folder
      files.push(relativePath.replace(/\\/g, '/')) // Ensure forward slashes
    }
  }
  
  return files
}

/**
 * Generate file tree structure for frontend consumption
 */
function generateFileTree(files, basePath) {
  const tree = {}
  
  files.forEach(file => {
    const parts = file.split('/')
    let current = tree
    
    parts.forEach((part, index) => {
      if (index === parts.length - 1) {
        // It's a file
        if (!current.files) current.files = []
        current.files.push(part)
      } else {
        // It's a directory
        if (!current.dirs) current.dirs = {}
        if (!current.dirs[part]) current.dirs[part] = {}
        current = current.dirs[part]
      }
    })
  })
  
  return tree
}

/**
 * Main function
 */
function generateManifest() {
  console.log('📂 Scanning public directory for files...')
  
  // Check if resources directory exists
  if (!fs.existsSync(RESOURCES_DIR)) {
    console.log('⚠️  Resources directory not found, creating it...')
    fs.mkdirSync(RESOURCES_DIR, { recursive: true })
  }
  
  // Scan resources directory
  const files = scanDirectory(RESOURCES_DIR, '')
  
  console.log(`✅ Found ${files.length} files`)
  
  // Generate manifest
  const manifest = {
    generated: new Date().toISOString(),
    basePath: '/resources',
    totalFiles: files.length,
    files: files,
    tree: generateFileTree(files, 'resources')
  }
  
  // Write manifest file
  fs.writeFileSync(MANIFEST_FILE, JSON.stringify(manifest, null, 2))
  
  console.log(`📝 Manifest written to ${MANIFEST_FILE}`)
  console.log('✨ Build complete!')
  
  // Display file tree for verification
  console.log('\n📊 File Structure:')
  files.forEach(file => {
    const depth = file.split('/').length - 1
    const indent = '  '.repeat(depth)
    const name = path.basename(file)
    console.log(`${indent}├─ ${name}`)
  })
}

// Run the script
try {
  generateManifest()
} catch (error) {
  console.error('❌ Error generating manifest:', error)
  process.exit(1)
}