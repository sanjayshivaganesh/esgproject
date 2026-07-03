export function normalizeText(text) {
  return String(text || '')
    .replace(/\r/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/\s+\n/g, '\n')
    .replace(/\n\s+/g, '\n')
    .trim()
}

export function compactText(text) {
  return normalizeText(text).replace(/\s+/g, ' ').trim()
}

export function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function countPhrase(text, phrase) {
  const normalized = compactText(text).toLowerCase()
  const pattern = new RegExp(`(^|[^a-z0-9])${escapeRegExp(phrase.toLowerCase())}([^a-z0-9]|$)`, 'g')
  return (normalized.match(pattern) || []).length
}

export function countPhrases(text, phrases) {
  return phrases.reduce((total, phrase) => total + countPhrase(text, phrase), 0)
}

export function collectPhraseHits(text, phrases, limit = 10) {
  return phrases
    .map((phrase) => ({
      phrase: typeof phrase === 'string' ? phrase : phrase.phrase,
      category: typeof phrase === 'string' ? undefined : phrase.category,
      severity: typeof phrase === 'string' ? 1 : phrase.severity,
      count: countPhrase(text, typeof phrase === 'string' ? phrase : phrase.phrase),
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count * b.severity - a.count * a.severity)
    .slice(0, limit)
}

export function countNumericalEvidence(text) {
  const normalized = compactText(text)
  const patterns = [
    /\b\d+(?:\.\d+)?\s?%/gi,
    /\b\d+(?:\.\d+)?\s?(?:percent|percentage points)\b/gi,
    /\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:tons?|tonnes?|metric tons?|mtco2e|tco2e|co2e)\b/gi,
    /\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:kg|kilograms?|kwh|mwh|gwh|mw|gw|liters?|litres?|gallons?|cubic meters?)\b/gi,
    /\bscope\s?[123]\b/gi,
    /\b(?:20\d{2}|19\d{2})\b/g,
  ]

  return patterns.reduce((total, pattern) => total + (normalized.match(pattern) || []).length, 0)
}

export function wordsPerThousand(count, wordCount) {
  return count / Math.max(1, wordCount / 1000)
}

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

export function round(value, digits = 2) {
  const scale = 10 ** digits
  return Math.round(value * scale) / scale
}
