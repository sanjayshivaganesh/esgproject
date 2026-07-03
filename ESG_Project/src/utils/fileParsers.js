import * as pdfjsLib from 'pdfjs-dist'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.mjs?url'
import { normalizeText } from './detectors'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker

function readAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}

function readAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsArrayBuffer(file)
  })
}

async function parsePdf(file) {
  const data = await readAsArrayBuffer(file)
  const pdf = await pdfjsLib.getDocument({ data }).promise
  const pages = []

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber)
    const content = await page.getTextContent()
    const pageText = content.items
      .map((item) => item.str)
      .join(' ')
      .replace(/(\w)-\s+(\w)/g, '$1$2')

    pages.push(normalizeText(pageText))
  }

  return normalizeText(pages.join('\n\n'))
}

async function parseDocx(file) {
  const data = await readAsArrayBuffer(file)
  
  // Use mammoth.js for DOCX parsing
  const mammoth = await import('mammoth')
  const result = await mammoth.extractRawText({ arrayBuffer: data })
  
  return normalizeText(result.value)
}

export async function parseFile(file) {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const type = file.type

  if (extension === 'pdf' || type === 'application/pdf') {
    return parsePdf(file)
  }

  if (extension === 'docx' || type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    return parseDocx(file)
  }

  if (extension === 'txt' || type.includes('text')) {
    return normalizeText(await readAsText(file))
  }

  throw new Error(`${file.name} is not a supported file. Please upload PDF, DOCX, or TXT files containing narrative text.`)
}

export async function parseFiles(files) {
  const parsed = await Promise.all(
    Array.from(files).map(async (file) => ({
      name: file.name,
      size: file.size,
      type: file.type || file.name.split('.').pop()?.toUpperCase() || 'Unknown',
      text: await parseFile(file),
    })),
  )

  return parsed.filter((file) => file.text.trim().length > 0)
}
