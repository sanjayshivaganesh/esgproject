import { controversyKeywords } from '../data/controversyKeywords.js'
import { evidenceKeywords } from '../data/evidenceKeywords.js'
import { promotionalKeywords } from '../data/promotionalKeywords.js'
import { broadClaimKeywords, hedgingKeywords, vagueKeywords } from '../data/vagueKeywords.js'
import {
  collectPhraseHits,
  compactText,
  countNumericalEvidence,
  countPhrases,
  escapeRegExp,
  round,
} from './detectors.js'

const bound01 = (value) => Math.max(0, Math.min(1, value))
const clampScore = (value) => Math.max(0, Math.min(100, Math.round(value)))

export function normalizeScore(value, { pivot = 1, mode = 'growth' } = {}) {
  const safeValue = Math.max(0, Number(value) || 0)
  const safePivot = Math.max(0.0001, pivot)
  const growth = 1 - Math.exp(-safeValue / safePivot)
  const normalized = mode === 'decay' ? 1 - growth : growth

  return Math.round(bound01(normalized) * 100)
}

function component(label, raw, pivot, weight, explanation, category) {
  const score = normalizeScore(raw, { pivot })

  return {
    label,
    raw: round(raw, 2),
    score,
    contribution: Math.round(score * weight),
    weight,
    explanation,
    category,
  }
}

function weightedAverage(items) {
  const totalWeight = items.reduce((sum, item) => sum + item.weight, 0)
  const weighted = items.reduce((sum, item) => sum + item.score * item.weight, 0)

  return Math.round(weighted / Math.max(1, totalWeight))
}

function countControversies(text) {
  const normalized = compactText(text).toLowerCase()
  const occupied = []
  const hits = []
  const sortedKeywords = [...controversyKeywords].sort((a, b) => b.phrase.length - a.phrase.length)

  sortedKeywords.forEach((keyword) => {
    const pattern = new RegExp(`(^|[^a-z0-9])${escapeRegExp(keyword.phrase.toLowerCase())}([^a-z0-9]|$)`, 'g')
    let count = 0
    let match = pattern.exec(normalized)

    while (match) {
      const start = match.index + match[1].length
      const end = start + keyword.phrase.length
      const overlaps = occupied.some((span) => start < span.end && end > span.start)

      if (!overlaps) {
        occupied.push({ start, end })
        count += 1
      }

      match = pattern.exec(normalized)
    }

    if (count > 0) hits.push({ ...keyword, count })
  })

  const count = hits.reduce((sum, hit) => sum + hit.count, 0)
  const severity = hits.reduce((sum, hit) => sum + hit.count * hit.severity, 0)
  const highSeverityCount = hits.reduce((sum, hit) => sum + (hit.severity >= 5 ? hit.count : 0), 0)
  const categories = new Set(hits.map((hit) => hit.category).filter(Boolean))
  const categoryCount = categories.size
  const severeGovernanceOrEnvironmental = hits.some(
    (hit) => hit.severity >= 5 && ['Governance controversy', 'Environmental controversy'].includes(hit.category),
  )

  return { hits, count, severity, highSeverityCount, categoryCount, severeGovernanceOrEnvironmental }
}

function confidenceLabel(score) {
  if (score >= 68) return 'High'
  if (score >= 38) return 'Medium'
  return 'Low'
}

function riskLabel(score) {
  if (score <= 30) return 'Low'
  if (score <= 60) return 'Moderate'
  return 'High'
}

const environmentalTopics = [
  'emissions',
  'ghg',
  'greenhouse gas',
  'carbon',
  'co2',
  'co2e',
  'renewable',
  'energy',
  'electricity',
  'waste',
  'water',
  'recycling',
  'pollution',
  'climate',
  'biodiversity',
  'deforestation',
  'landfill',
]

const outcomeTerms = [
  'reduced',
  'reduction',
  'decreased',
  'lowered',
  'cut',
  'achieved',
  'improved',
  'eliminated',
  'avoided',
  'diverted',
  'replenished',
  'recycled',
  'captured',
  'restored',
  'mitigated',
  'conserved',
  'protected',
  'removed',
  'abated',
  'generated',
  'procured',
]

const futureTerms = [
  'aim to',
  'plan to',
  'intend to',
  'seek to',
  'working toward',
  'working towards',
  'target',
  'goal',
  'roadmap',
  'expected to',
  'on track to',
  'aspire to',
  'will reduce',
  'will achieve',
  'by 2030',
  'by 2040',
  'by 2050',
]

const strongAchievementTerms = [
  'achieved zero waste certification',
  'achieved zero waste',
  'zero waste certification',
  'certified zero waste',
  'landfill free',
  'eliminated single-use plastic',
  'completed remediation',
  'restored habitat',
  'protected habitat',
]

const quantitativePattern =
  /\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:%|percent|percentage points?|tons?|tonnes?|metric tons?|mtco2e|tco2e|co2e|kg|kilograms?|kwh|mwh|gwh|mw|gw|liters?|litres?|gallons?|m3|cubic meters?|hectares?|acres?)\b/i

function splitSentences(text) {
  return compactText(text)
    .toLowerCase()
    .split(/[.!?]+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
}

function extractOutcomeEvidence(text) {
  const sentences = splitSentences(text)
  const evidenceSentences = []
  let quantitativeOutcomes = 0
  let strongAchievements = 0

  sentences.forEach((sentence) => {
    const hasTopic = environmentalTopics.some((term) => sentence.includes(term))
    const hasOutcome = outcomeTerms.some((term) => sentence.includes(term))
    const hasFuture = futureTerms.some((term) => sentence.includes(term))
    const hasQuantity = quantitativePattern.test(sentence)
    const hasStrongAchievement = strongAchievementTerms.some((term) => sentence.includes(term))

    if (!hasTopic || !hasOutcome || hasFuture) return

    if (hasQuantity) {
      quantitativeOutcomes += 1
      evidenceSentences.push(sentence)
    } else if (hasStrongAchievement) {
      strongAchievements += 1
      evidenceSentences.push(sentence)
    }
  })

  return {
    quantitativeOutcomes,
    strongAchievements,
    environmentalOutcomes: quantitativeOutcomes + strongAchievements,
    evidenceSentences: evidenceSentences.slice(0, 8),
  }
}

function supportCategory(ratio) {
  if (ratio < 0.5) return 'weak support'
  if (ratio <= 1) return 'moderate support'
  return 'strong support'
}

function transparencyScoreFromSignals({ methodologySignals, assuranceSignals, scopeCoverage }) {
  const frameworkCoverage = Math.min(methodologySignals / Math.max(1, evidenceKeywords.methodologyTerms.length), 1) * 100
  const assuranceCoverage = Math.min(assuranceSignals / 2, 1) * 100
  const scopeCoverageScore = Math.min(scopeCoverage / 3, 1) * 100

  return clampScore(
    frameworkCoverage * 0.3 +
      assuranceCoverage * 0.5 +
      scopeCoverageScore * 0.2,
  )
}

function sanityCheckRisk({ risk, evidenceSignal, transparencyScore, supportRatio, controversyCount }) {
  if (supportRatio > 1 && evidenceSignal > 80 && transparencyScore > 80 && controversyCount === 0) {
    return Math.min(risk, 40)
  }

  return risk
}

function classifyDocument(text, { methodologySignals, assuranceSignals, scopeCoverage, outcomeEvidence, promotionalCount }) {
  const normalized = compactText(text).toLowerCase()
  const reportTerms = countPhrases(normalized, [
    'annual report',
    'esg report',
    'sustainability report',
    'reporting period',
    'materiality',
    'performance data',
    'kpi',
  ])
  const pressTerms = countPhrases(normalized, [
    'press release',
    'announced today',
    'news release',
    'media contact',
    'investor relations',
    'forward-looking statements',
  ])
  const marketingTerms =
    promotionalCount +
    countPhrases(normalized, ['our commitment', 'our approach', 'learn more', 'we believe'])
  const structureScore =
    methodologySignals + assuranceSignals + scopeCoverage + Math.min(5, outcomeEvidence.environmentalOutcomes) + reportTerms

  if (normalized.includes('esg report') || structureScore >= 8) return 'ESG Report'
  if (normalized.includes('sustainability report') || structureScore >= 5) return 'Sustainability Report'
  if (pressTerms >= 2) return 'Press Release'
  if (marketingTerms >= 3 && structureScore < 5) return 'Marketing / Sustainability Page'
  return 'Unknown'
}

function confidenceExplanation(label, components = {}, files = []) {
  const fileCount = files.length
  const fileText = fileCount <= 1 ? 'a single uploaded report' : `${fileCount} uploaded reports`
  const fileVerb = fileCount <= 1 ? 'contains' : 'contain'
  const fileProvide = fileCount <= 1 ? 'provides' : 'provide'
  const weakest = Object.entries(components)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 2)
    .map(([key]) => key.replace(/([A-Z])/g, ' $1').toLowerCase())
    .join(' and ')

  if (label === 'High') {
    return `Confidence is high because ${fileText} ${fileProvide} broad coverage, measurable evidence, diverse evidence categories, and stable signal composition.`
  }

  if (label === 'Medium') {
    return `Confidence is medium because ${fileText} ${fileVerb} usable signals, while ${weakest || 'coverage or signal stability'} remain only partial.`
  }

  return `Confidence is low because ${fileText} ${fileProvide} limited coverage, sparse measurable evidence, narrow evidence diversity, or unstable component signals.`
}

function formatScopeCoverage(count) {
  const detected = Math.max(0, Math.min(3, Number(count) || 0))
  return {
    detected,
    label: detected === 0 ? 'None detected' : `${detected} of 3 detected`,
    summary: `${detected} of 3 scopes reported`,
  }
}

function describeStrongSignals(components, direction = 'strong') {
  const sorted = [...components].sort((a, b) => (direction === 'weak' ? a.score - b.score : b.score - a.score))
  return sorted
    .slice(0, 2)
    .map((item) => item.label.toLowerCase())
    .join(' and ')
}

function controversyExplanation(controversy) {
  if (controversy.count === 0) {
    return 'No material controversy indicators were detected in the uploaded documents.'
  }

  const categoryText = [...new Set(controversy.hits.map((hit) => hit.category).filter(Boolean))]
    .slice(0, 2)
    .join(' and ')
    .toLowerCase()
  const severityText =
    controversy.highSeverityCount > 0
      ? 'The analysis treated this as a stronger caution signal because at least one indicator was high severity.'
      : 'The analysis treated this as a caution signal without letting a single low-context mention dominate the result.'

  return `${controversy.count} controversy indicator${controversy.count === 1 ? '' : 's'} appeared${categoryText ? ` across ${categoryText}` : ''}. ${severityText}`
}

function buildSummary(result) {
  const riskPhrase = `${result.riskLevel.toLowerCase()} greenwashing risk`
  const claimReason = result.claimSignal >= 70 ? 'strong sustainability positioning' : result.claimSignal >= 40 ? 'moderate sustainability positioning' : 'limited sustainability positioning'
  const evidenceReason = result.evidenceSignal >= 70 ? 'strong evidence support' : result.evidenceSignal >= 40 ? 'mixed evidence support' : 'weak evidence support'
  const strongestEvidence = describeStrongSignals(result.evidenceComponents)
  const weakestEvidence = describeStrongSignals(result.evidenceComponents, 'weak')
  const controversyReason = controversyExplanation(result.controversy)

  return `The uploaded material shows ${claimReason} with ${evidenceReason}. The greenwashing gap is ${result.greenwashingGap}/100, reflecting unsupported claim intensity only, while unsupported claim pressure is ${result.unsupportedClaimRatio}% after considering evidence breadth and transparency quality. Evidence is strongest in ${strongestEvidence || 'detected reporting signals'} and weakest in ${weakestEvidence || 'supporting disclosures'}. This produces a ${riskPhrase}. ${controversyReason}`
}

function driver(label, value, category, explanation, polarity) {
  return { label, value: Math.round(value), category, explanation, polarity }
}

export function runGreenwashingAnalysis({ companyName, parsedFiles }) {
  const files = parsedFiles || []
  const combinedText = compactText(files.map((file) => file.text).join('\n\n'))
  const wordCount = combinedText ? combinedText.split(/\s+/).length : 0
  const perThousand = Math.max(1, wordCount / 1000)
  const textLength = combinedText.length

  const vagueCount = countPhrases(combinedText, vagueKeywords)
  const broadClaimCount = countPhrases(combinedText, broadClaimKeywords)
  const hedgingCount = countPhrases(combinedText, hedgingKeywords)
  const promotionalCount = countPhrases(combinedText, promotionalKeywords)
  const climateCommitmentCount = countPhrases(combinedText, [
    'net zero',
    'carbon neutral',
    'climate positive',
    'decarbonization',
    'low-carbon future',
    'climate action',
    'clean energy',
    'sustainable energy',
    'energy transition',
    'electrification',
    'zero emissions',
    'zero-emissions',
    'zero emission',
    'low emission',
    'low-emission',
    'carbon-free',
  ])
  const positiveAssertionCount = broadClaimCount + vagueCount + Math.ceil(hedgingCount * 0.75)

  const rawNumericalMetricsCount = countNumericalEvidence(combinedText)
  const outcomeEvidence = extractOutcomeEvidence(combinedText)
  const numericalMetricsCount = outcomeEvidence.quantitativeOutcomes
  const environmentalMetricsCount = outcomeEvidence.environmentalOutcomes
  const methodologySignals = countPhrases(combinedText, evidenceKeywords.methodologyTerms)
  const assuranceSignals =
    countPhrases(combinedText, evidenceKeywords.auditTerms) +
    countPhrases(combinedText, evidenceKeywords.verificationTerms)
  const scopeCoverage = ['scope 1', 'scope 2', 'scope 3'].filter((phrase) => countPhrases(combinedText, [phrase]) > 0).length

  const claimComponents = [
    component(
      'Sustainability Phrase Density',
      vagueCount / perThousand,
      7,
      0.2,
      'Measures how frequently broad sustainability language appears relative to document size.',
      'Claims',
    ),
    component(
      'Climate Commitment Language',
      climateCommitmentCount / perThousand,
      4.5,
      0.18,
      'Measures explicit net-zero, carbon-neutral, and climate commitment language without dominating the claim score.',
      'Claims',
    ),
    component(
      'Marketing Language Density',
      promotionalCount / perThousand,
      2.5,
      0.18,
      'Measures corporate PR intensity and superlative framing.',
      'Claims',
    ),
    component(
      'Promotional ESG Language',
      (promotionalCount + vagueCount * 0.6) / perThousand,
      6,
      0.16,
      'Combines ESG wording with promotional tone to identify narrative-heavy reporting.',
      'Claims',
    ),
    component(
      'Positive Sustainability Assertions',
      positiveAssertionCount / perThousand,
      9,
      0.22,
      'Measures the total volume of positive sustainability assertions and future-facing commitments.',
      'Claims',
    ),
  ]

  const evidenceDiversity = [
    outcomeEvidence.quantitativeOutcomes > 0,
    outcomeEvidence.strongAchievements > 0,
    scopeCoverage >= 2,
  ].filter(Boolean).length
  const disclosureCompletenessRaw =
    evidenceDiversity + Math.min(1.5, scopeCoverage * 0.5)
  const disclosureCompletenessScore = normalizeScore(disclosureCompletenessRaw, { pivot: 4.2 })
  const rawEvidenceUnits =
    outcomeEvidence.quantitativeOutcomes * 1.4 +
    outcomeEvidence.strongAchievements * 1.2
  const evidenceUnits = rawEvidenceUnits

  const evidenceComponents = [
    component(
      'Numerical Evidence',
      outcomeEvidence.quantitativeOutcomes / perThousand,
      8,
      0.48,
      'Scores quantified environmental outcome sentences, excluding future targets and framework references.',
      'Evidence',
    ),
    component(
      'Environmental Outcomes',
      environmentalMetricsCount / perThousand,
      7,
      0.32,
      'Scores environmental outcomes tied to actions such as reductions, diversion, recycling, restoration, or achievement.',
      'Evidence',
    ),
    component(
      'Strong Achievements',
      outcomeEvidence.strongAchievements / perThousand,
      2.5,
      0.2,
      'Scores strong completed achievements such as zero waste certification or completed restoration.',
      'Evidence',
    ),
  ]

  const transparencyComponents = [
    component(
      'Methodology Disclosure',
      methodologySignals / perThousand,
      2.5,
      0.38,
      'Detects reporting boundaries, calculation basis, GHG Protocol, SASB, TCFD, GRI, CDP, and disclosed methods.',
      'Transparency',
    ),
    component(
      'Assurance Coverage',
      assuranceSignals / perThousand,
      1.8,
      0.38,
      'Detects audits, assurance statements, independent verification, and third-party assessment.',
      'Transparency',
    ),
    component(
      'Disclosure Completeness',
      disclosureCompletenessRaw,
      4.2,
      0.24,
      'Rewards breadth across outcome evidence and Scope 1/2/3 coverage.',
      'Transparency',
    ),
  ]

  const claimSignal = weightedAverage(claimComponents)
  const evidenceSignal = weightedAverage(evidenceComponents)
  const transparencyScore = transparencyScoreFromSignals({
    methodologySignals,
    assuranceSignals,
    scopeCoverage,
  })
  const claimCredibility = clampScore(evidenceSignal * 0.6 + transparencyScore * 0.4)
  const claimShortfall = Math.max(0, claimSignal - evidenceSignal)
  const greenwashingGap = clampScore(claimShortfall)
  const supportRatio = round(evidenceSignal / Math.max(claimSignal, 1), 2)
  const supportRatioCategory = supportCategory(supportRatio)
  const transparencyWeakness = Math.max(0, 100 - ((methodologySignals > 0 ? 50 : 0) + (assuranceSignals > 0 ? 50 : 0)))
  const transparencyPenalty = normalizeScore(Math.max(0, 55 - evidenceSignal), { pivot: 42 })
  const unsupportedClaimRatio = clampScore(
    claimShortfall * 0.55 +
      greenwashingGap * 0.35 +
      Math.max(0, claimSignal - 55) * 0.15 +
      transparencyPenalty * 0.2 +
      transparencyWeakness * 0.2,
  )
  const supportedClaimRatio = clampScore(100 - unsupportedClaimRatio)

  const controversies = countControversies(combinedText)
  const controversyPenaltyRaw =
    Math.sqrt(controversies.severity) * (controversies.severeGovernanceOrEnvironmental ? 9 : 4.5) +
    controversies.highSeverityCount * 4 +
    Math.max(0, controversies.count - 2) * 2
  const controversyPenaltyScore = normalizeScore(controversyPenaltyRaw, { pivot: 30 })
  const supportRatioPenalty = supportRatio < 0.5 ? 50 : supportRatio < 1 ? 25 : 0
  const transparencyBonus = transparencyScore * 0.3
  const evidenceBonus = evidenceSignal * 0.4
  const claimPromotionalWeight = Math.min(25, promotionalCount * 5)
  const controversyPenalty = Math.min(40, controversies.count * 12 || controversyPenaltyScore * 0.4)
  const rawRisk =
    supportRatioPenalty +
    greenwashingGap * 0.5 +
    claimPromotionalWeight +
    controversyPenalty -
    transparencyBonus -
    evidenceBonus
  const greenwashingRisk = clampScore(
    sanityCheckRisk({
      risk: rawRisk,
      evidenceSignal,
      transparencyScore,
      supportRatio,
      controversyCount: controversies.count,
    }),
  )
  const riskLevel = riskLabel(greenwashingRisk)

  const documentType = classifyDocument(combinedText, {
    methodologySignals,
    assuranceSignals,
    scopeCoverage,
    outcomeEvidence,
    promotionalCount,
  })
  const reportCountScore = normalizeScore(files.length, { pivot: 2.2 })
  const coverageScore = Math.round(
    Math.min(100, methodologySignals * 12 + assuranceSignals * 16 + scopeCoverage * 12 + environmentalMetricsCount * 8),
  )
  const evidenceQuantityScore = normalizeScore(evidenceUnits, { pivot: 42 })
  const diversityScore = Math.round((evidenceDiversity / 3) * 100)
  const componentScores = [...claimComponents, ...evidenceComponents, ...transparencyComponents].map((item) => item.score)
  const averageComponentScore = componentScores.reduce((sum, score) => sum + score, 0) / Math.max(1, componentScores.length)
  const variance =
    componentScores.reduce((sum, score) => sum + (score - averageComponentScore) ** 2, 0) /
    Math.max(1, componentScores.length)
  const stabilityScore = Math.max(0, Math.round(100 - Math.sqrt(variance)))
  const confidenceScore = Math.round(
    coverageScore * 0.24 +
      evidenceQuantityScore * 0.24 +
      diversityScore * 0.2 +
      reportCountScore * 0.16 +
      stabilityScore * 0.16,
  )
  const confidenceLevel = confidenceLabel(confidenceScore)

  const claimIntensityDrivers = [...claimComponents]
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3)
    .map((item) => driver(item.label, item.contribution, 'Claim Intensity', item.explanation, 'claim'))
  const evidenceStrengthDrivers = [...evidenceComponents]
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3)
    .map((item) => driver(item.label, item.contribution, 'Evidence Strength', item.explanation, 'evidence'))
  const credibilityDrivers = [...transparencyComponents]
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3)
    .map((item) => driver(item.label, item.contribution, 'Credibility', item.explanation, 'credibility'))
  const riskDrivers = [
    ...(controversies.count > 0
      ? [
          driver(
            'Controversy Exposure',
            controversyPenaltyScore,
            'Risk',
            'Legal, regulatory, labor, corruption, or environmental controversy terms increase risk, with high-severity categories weighted more strongly.',
            'risk',
          ),
        ]
      : []),
    ...(evidenceSignal < 45
      ? [
          driver(
            'Evidence Gaps',
            transparencyPenalty,
            'Risk',
            'Outcome evidence is not strong enough to support the claim intensity.',
            'risk',
          ),
        ]
      : []),
    ...(unsupportedClaimRatio >= 30
      ? [
          driver(
            'Unsupported Claims',
            unsupportedClaimRatio,
            'Risk',
            'A large share of claim intensity is not matched by detected evidence or transparency quality.',
            'risk',
          ),
        ]
      : []),
  ].sort((a, b) => b.value - a.value)

  const result = {
    engineVersion: 'DocumentDrivenV1',
    companyName: companyName?.trim() || 'Target Entity',
    claimSignal,
    evidenceSignal,
    transparencyScore,
    claimCredibility,
    documentType,
    greenwashingGap,
    supportRatio,
    supportRatioCategory,
    greenwashingRisk,
    riskScore: greenwashingRisk,
    riskLevel,
    confidenceLevel,
    confidenceScore,
    confidenceReason: confidenceExplanation(confidenceLevel, {
      documentCoverage: coverageScore,
      evidenceQuantity: evidenceQuantityScore,
      evidenceDiversity: diversityScore,
      reportCount: reportCountScore,
      signalStability: stabilityScore,
    }, files),
    confidenceComponents: {
      documentCoverage: coverageScore,
      evidenceQuantity: evidenceQuantityScore,
      evidenceDiversity: diversityScore,
      reportCount: reportCountScore,
      signalStability: stabilityScore,
    },
    unsupportedClaimRatio,
    supportedClaimRatio,
    claimComponents,
    evidenceComponents,
    transparencyComponents,
    evidenceBreakdown: {
      numericalMetrics: numericalMetricsCount,
      environmentalMetrics: environmentalMetricsCount,
      methodologySignals,
      assuranceSignals,
      quantitativeOutcomes: outcomeEvidence.quantitativeOutcomes,
      strongAchievements: outcomeEvidence.strongAchievements,
      evidenceSentences: outcomeEvidence.evidenceSentences,
      scopeCoverage,
      scopeCoverageDisplay: formatScopeCoverage(scopeCoverage),
      disclosureCompleteness: disclosureCompletenessScore,
      totalEvidenceUnits: round(evidenceUnits, 1),
    },
    controversy: {
      count: controversies.count,
      severity: controversies.severity,
      highSeverityCount: controversies.highSeverityCount,
      penaltyScore: controversyPenaltyScore,
      hits: controversies.hits,
    },
    controversyCount: controversies.count,
    claimIntensityDrivers,
    evidenceStrengthDrivers,
    credibilityDrivers,
    riskDrivers,
    flaggedPhrases: [
      ...collectPhraseHits(combinedText, [...vagueKeywords, ...hedgingKeywords, ...promotionalKeywords], 8),
      ...controversies.hits.slice(0, 6),
    ].slice(0, 10),
    positiveIndicators: collectPhraseHits(
      combinedText,
      [
        ...evidenceKeywords.metricTerms,
        ...evidenceKeywords.auditTerms,
        ...evidenceKeywords.verificationTerms,
        ...evidenceKeywords.methodologyTerms,
      ],
      10,
    ),
    files,
    signals: {
      textLength,
      wordCount,
      vagueCount,
      broadClaimCount,
      hedgingCount,
      promotionalCount,
      climateCommitmentCount,
      positiveAssertionCount,
      numericalMetricsCount,
      rawNumericalMetricsCount,
      environmentalMetricsCount,
      methodologySignals,
      assuranceSignals,
      evidenceUnits,
      transparencyScore,
      supportRatio,
      supportRatioCategory,
      documentType,
    },
  }

  return {
    ...result,
    summary: buildSummary(result),
  }
}

export const runEsgAnalysis = runGreenwashingAnalysis
