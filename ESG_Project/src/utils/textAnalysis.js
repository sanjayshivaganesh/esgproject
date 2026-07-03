import { sustainabilityKeywords } from '../data/sustainabilityKeywords'

export function normalizeText(text) {
  return String(text || '').replace(/\s+/g, ' ').trim()
}

export function countOccurrences(text, phrases) {
  const lowerText = normalizeText(text).toLowerCase()

  return phrases.reduce((total, phrase) => {
    const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const pattern = new RegExp(`\\b${escaped}\\b`, 'gi')
    return total + (lowerText.match(pattern) || []).length
  }, 0)
}

export function collectPhraseHits(text, phrases, limit = 8) {
  const lowerText = normalizeText(text).toLowerCase()

  return phrases
    .map((phrase) => ({
      phrase,
      count: countOccurrences(lowerText, [phrase]),
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
}

export function countNumericalClaims(text) {
  const normalized = normalizeText(text)
  const numberMatches =
    normalized.match(/\b\d+(?:\.\d+)?\s?(?:%|percent|tons?|tonnes?|mtco2e|kg|kwh|mwh|gwh|liters?|gallons?|years?|million|billion)?\b/gi) || []

  return numberMatches.length
}

export function analyzeTextSignals(text) {
  const normalized = normalizeText(text)

  return {
    textLength: normalized.length,
    vagueCount: countOccurrences(normalized, sustainabilityKeywords.vague),
    broadClaimCount: countOccurrences(normalized, sustainabilityKeywords.broadClaims),
    numericalClaimCount: countNumericalClaims(normalized),
    hedgingCount: countOccurrences(normalized, sustainabilityKeywords.hedging),
    promotionalCount: countOccurrences(normalized, sustainabilityKeywords.promotional),
    metricsCount: countOccurrences(normalized, sustainabilityKeywords.metrics),
    transparencyCount: countOccurrences(normalized, sustainabilityKeywords.transparency),
    controversyCount: countOccurrences(normalized, sustainabilityKeywords.controversies),
    flaggedPhrases: collectPhraseHits(normalized, [
      ...sustainabilityKeywords.vague,
      ...sustainabilityKeywords.hedging,
      ...sustainabilityKeywords.promotional,
      ...sustainabilityKeywords.controversies,
    ]),
    positiveIndicators: collectPhraseHits(normalized, [
      ...sustainabilityKeywords.metrics,
      ...sustainabilityKeywords.transparency,
    ]),
  }
}
