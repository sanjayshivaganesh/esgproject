import { useState } from 'react'
import ScoreCard from './ScoreCard'

function SmallMetric({ label, value, explanation, suffix = '', muted = false }) {
  return (
    <div className="rounded-xl border border-line bg-white/40 p-5" title={explanation}>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
      <div className={`mt-3 wrap-break-word text-xl md:text-2xl font-semibold leading-tight tracking-tight ${muted ? 'text-muted' : 'text-ink'}`}>
        {value}
        {suffix ? <span className="ml-1">{suffix}</span> : null}
      </div>
      <p className="mt-2 text-[11px] leading-4 text-muted">{explanation}</p>
    </div>
  )
}

function VerdictBanner({ riskLevel, confidenceScore, explanation }) {
  const riskColors = {
    High: 'bg-red-50 border-red-200 text-red-900',
    Medium: 'bg-amber-50 border-amber-200 text-amber-900',
    Low: 'bg-green-50 border-green-200 text-green-900',
  }

  const confidenceLabel = confidenceScore >= 70 ? 'High' : confidenceScore >= 50 ? 'Medium' : 'Low'

  return (
    <div className={`rounded-2xl border p-6 md:p-8 ${riskColors[riskLevel]}`}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center rounded-full bg-white/50 px-3 py-1 text-xs font-semibold uppercase tracking-wide">
              Overall Verdict
            </span>
            <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${riskColors[riskLevel]}`}>
              {riskLevel} Risk
            </span>
          </div>
          <h2 className="mt-3 text-2xl font-semibold md:text-3xl">
            {riskLevel} Greenwashing Risk
          </h2>
          <p className="mt-2 text-sm md:text-base opacity-90">
            {explanation}
          </p>
        </div>
        <div className="flex flex-col gap-2 md:text-right">
          <div className="text-sm opacity-90">Evidence Quality</div>
          <div className="text-2xl font-semibold">{confidenceLabel}</div>
          <div className="text-sm opacity-75">Based on data completeness in this document</div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, explanation, interpretation, color, icon }) {
  const colorClasses = {
    green: 'bg-green-50 border-green-200 text-green-900',
    amber: 'bg-amber-50 border-amber-200 text-amber-900',
    red: 'bg-red-50 border-red-200 text-red-900',
    neutral: 'bg-gray-50 border-gray-200 text-gray-900',
  }

  return (
    <div className={`rounded-xl border p-5 ${colorClasses[color] || colorClasses.neutral}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-75">{title}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
          <p className="mt-2 text-sm leading-5 opacity-90">{explanation}</p>
        </div>
        {icon && (
          <div className="flex-shrink-0 text-2xl opacity-75">{icon}</div>
        )}
      </div>
      {interpretation && (
        <div className="mt-3 rounded-lg bg-white/50 p-3 text-xs font-medium">
          {interpretation}
        </div>
      )}
    </div>
  )
}

function ProgressBar({ value, max = 100, color = 'neutral' }) {
  const percentage = Math.min((value / max) * 100, 100)
  const colorClasses = {
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
    neutral: 'bg-gray-400',
  }

  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div
        className={`h-full rounded-full transition-all duration-500 ${colorClasses[color] || colorClasses.neutral}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}

function CollapsibleSection({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="rounded-xl border border-line bg-white/40">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-5 text-left transition-colors hover:bg-white/60"
      >
        <p className="text-sm font-semibold uppercase tracking-wide text-muted">{title}</p>
        <svg
          className={`h-5 w-5 transform transition-transform text-muted ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && <div className="border-t border-line p-5">{children}</div>}
    </div>
  )
}

function normalizeResult(result) {
  if (!result) return null

  const rule = result.rule || {}
  const signals = rule.signals || {}
  const indicators = rule.indicators || {}
  const sentenceClassification = rule.sentence_classification || {}
  const classificationBreakdown = sentenceClassification.classification_breakdown || {}
  const supportRatioExplanation = rule.support_ratio_explanation || {}
  const outcomeEvidence = rule.outcome_evidence || {}

  return {
    companyName: result.companyName || 'Uploaded Report',

    greenwashingRisk: Math.round(rule.risk ?? 0),
    riskLevel:
      (rule.risk ?? 0) > 60
        ? 'High'
        : (rule.risk ?? 0) > 30
        ? 'Medium'
        : 'Low',

    claimPressure: Math.round(rule.claim_pressure ?? 0),
    outcomeEvidence: Math.round(outcomeEvidence.outcome_evidence_score ?? 0),
    transparencyScore: Math.round(rule.transparency_score ?? 0),
    confidenceScore: Math.round(rule.confidence_score ?? 0),
    documentType: rule.document_type ?? 'UNKNOWN',
    supportRatio: Number(rule.support_ratio ?? 0),
    supportRatioCategory: rule.support_ratio_category ?? 'weak support',
    greenwashingGap: Math.round(rule.greenwashing_gap ?? 0),
    futureTargetDensity: Math.round(rule.future_target_density ?? 0),

    summary: result.fusion?.verdict ?? 'No summary available',

    controversyCount: rule.controversy?.count ?? 0,
    controversyHits: signals.controversy_keywords ?? {},

    indicators: {
      claimLanguage: signals.claim_keywords ?? indicators.claim_language_frequencies ?? {},
      transparency: signals.transparency_keywords ?? indicators.transparency_frequencies ?? {},
      outcome: signals.outcome_keywords ?? indicators.outcome_frequencies ?? {},
    },

    drivers: {
      claim: rule.drivers?.claim ?? [],
      outcome: rule.drivers?.outcome ?? [],
      transparency: rule.drivers?.transparency ?? [],
      risk: rule.drivers?.risk ?? [],
    },

    outcomeBreakdown: {
      outcomeCount: outcomeEvidence.real_outcome_count ?? classificationBreakdown.outcome_count ?? 0,
      quantifiedOutcomes: outcomeEvidence.quantified_outcomes_count ?? 0,
      strongAchievements: outcomeEvidence.strong_achievements ?? 0,
      targetSentences: classificationBreakdown.target_count ?? rule.claim?.target_sentence_count ?? 0,
    },

    supportRatioDetails: {
      totalTargets: supportRatioExplanation.number_of_targets ?? 0,
      supportedTargets: supportRatioExplanation.supported_targets ?? 0,
      unsupportedTargets: supportRatioExplanation.unsupported_targets ?? 0,
      percentageSupported: supportRatioExplanation.percentage_supported ?? 0,
      averageMatchScore: supportRatioExplanation.average_match_score ?? 0,
    },

    files: result.files ?? null,
  }
}

function ComponentRows({ title, items, rawCounts = {} }) {
  return (
    <div className="card-qml p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="grid grid-cols-[1fr_auto] items-center gap-4 border-b border-line pb-3 text-sm"
            title={item.explanation}
          >
            <span className="min-w-0">
              <span className="block font-medium text-ink">{item.label}</span>
              <span className="mt-1 block text-xs leading-5 text-muted">{item.explanation}</span>

              {rawCounts[item.label] !== undefined ? (
                <span className="mt-1 block text-xs font-medium text-muted">
                  Raw count: {rawCounts[item.label]}
                </span>
              ) : null}
            </span>

            <span className="font-mono text-xs md:text-sm font-semibold text-ink text-right wrap-break-word max-w-22.5 md:max-w-none">
              {item.score <= 0 ? 'Not Detected' : `${(item.score / 10).toFixed(1)} / 10`}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ListCard({ title, items, emptyText }) {
  const entries = Array.isArray(items)
    ? items.map((item) => [item, null])
    : Object.entries(items || {})

  return (
    <div className="card-qml p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>

      {entries.length ? (
        <ul className="mt-4 space-y-2 text-sm text-ink">
          {entries.map(([label, count]) => (
            <li key={label} className="wrap-break-word">
              • {label}
              {count !== null ? ` (${count})` : ''}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-muted">{emptyText}</p>
      )}
    </div>
  )
}

function ResultsPage({ result, onNavigate }) {
  const data = normalizeResult(result)
  if (!data) {
    return (
      <div className="page-section">
        <section className="border-b border-line py-20 md:py-24">
          <div className="container-qml">
            <div className="card-qml max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
                Analysis Output
              </p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
                No greenwashing analysis yet.
              </h1>
              <p className="mt-4 leading-7 text-muted">
                Upload a PDF, TXT, or CSV file and run analysis.
              </p>

              <button
                type="button"
                onClick={() => onNavigate('input')}
                className="mt-8 inline-flex items-center rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition-all hover:bg-neutral-800"
              >
                Start Analysis
              </button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  const riskTone =
    data.greenwashingRisk > 60
      ? 'red'
      : data.greenwashingRisk > 30
      ? 'amber'
      : 'green'

  // Generate plain English explanation based on metrics
  const generateVerdictExplanation = () => {
    if (data.greenwashingRisk > 60) {
      if (data.claimPressure > data.outcomeEvidence + 30) {
        return "The report makes many environmental claims but provides limited measurable evidence to support them."
      } else if (data.supportRatio < 0.5) {
        return "Most sustainability targets lack supporting evidence of actual achievement."
      } else {
        return "The company's environmental claims significantly exceed their documented performance."
      }
    } else if (data.greenwashingRisk > 30) {
      return "The report contains a moderate level of unsupported sustainability claims."
    } else {
      return "The company's environmental claims are generally supported by measurable evidence."
    }
  }

  // Generate executive reasoning summary
  const generateReasoningSummary = () => {
    const bullets = []

    // Claims detected
    if (data.claimPressure > 50) {
      bullets.push({ icon: '📢', text: `Many sustainability claims were identified (intensity: ${data.claimPressure}/100).` })
    } else if (data.claimPressure > 25) {
      bullets.push({ icon: '📢', text: `Moderate sustainability claims were identified (intensity: ${data.claimPressure}/100).` })
    } else {
      bullets.push({ icon: '📢', text: `Limited sustainability claims were identified (intensity: ${data.claimPressure}/100).` })
    }

    // Support ratio
    const supportedPercent = data.supportRatioDetails.percentageSupported
    if (supportedPercent >= 75) {
      bullets.push({ icon: '✓', text: `Most targets (${supportedPercent.toFixed(0)}%) were supported by measurable evidence.` })
    } else if (supportedPercent >= 50) {
      bullets.push({ icon: '✓', text: `Approximately half of targets (${supportedPercent.toFixed(0)}%) were supported by measurable evidence.` })
    } else if (supportedPercent > 0) {
      bullets.push({ icon: '⚠', text: `Few targets (${supportedPercent.toFixed(0)}%) were supported by measurable evidence.` })
    } else {
      bullets.push({ icon: '⚠', text: `No targets were supported by measurable evidence.` })
    }

    // Evidence strength
    if (data.outcomeEvidence > 60) {
      bullets.push({ icon: '✓', text: `Strong evidence of past environmental performance was detected (${data.outcomeEvidence}/100).` })
    } else if (data.outcomeEvidence > 30) {
      bullets.push({ icon: '⚠', text: `Moderate evidence of past environmental performance was detected (${data.outcomeEvidence}/100).` })
    } else {
      bullets.push({ icon: '⚠', text: `Limited evidence of past environmental performance was detected (${data.outcomeEvidence}/100).` })
    }

    // Future targets
    if (data.futureTargetDensity > 50) {
      bullets.push({ icon: '⚠', text: `Many future targets were identified without current achievement data.` })
    } else if (data.futureTargetDensity > 25) {
      bullets.push({ icon: '⚠', text: `Some future targets were identified with limited current achievement data.` })
    }

    // Transparency
    if (data.transparencyScore > 50) {
      bullets.push({ icon: '✓', text: `Transparency indicators (frameworks, assurance, scope) were present (${data.transparencyScore}/100).` })
    }

    // Controversy
    if (data.controversyCount > 0) {
      bullets.push({ icon: '⚠', text: `Controversy language was detected within this document (${data.controversyCount} signals).` })
    } else {
      bullets.push({ icon: '✓', text: `No controversy language was detected within this document.` })
    }

    return bullets
  }

  return (
    <div className="page-section">
      <section className="border-b border-line py-16 md:py-20">
        <div className="container-qml space-y-8">

          <div className="flex flex-col items-start justify-between border-b border-line pb-8 md:flex-row md:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
                Analysis Output
              </p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
                Greenwashing Analysis
              </h1>
              <p className="mt-2 text-sm text-muted">
                {data.companyName}
              </p>
            </div>
          </div>

          {/* SECTION 1: Overall Verdict */}
          <VerdictBanner
            riskLevel={data.riskLevel}
            confidenceScore={data.confidenceScore}
            explanation={generateVerdictExplanation()}
          />

          {/* SECTION 1.5: Executive Reasoning Summary */}
          <div className="rounded-xl border border-line bg-white/40 p-6">
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">Analysis Reasoning</h3>
            <ul className="space-y-3">
              {generateReasoningSummary().map((bullet, index) => (
                <li key={index} className="flex items-start gap-3 text-sm">
                  <span className="flex-shrink-0 text-lg">{bullet.icon}</span>
                  <span className="text-ink">{bullet.text}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 pt-4 border-t border-line">
              <p className="text-sm font-medium text-ink">
                Overall: This combination results in a <span className={`font-semibold ${data.riskLevel === 'High' ? 'text-red-600' : data.riskLevel === 'Medium' ? 'text-amber-600' : 'text-green-600'}`}>{data.riskLevel} Greenwashing Risk</span>.
              </p>
            </div>
          </div>

          {/* SECTION 2: Key Metrics */}
          <div>
            <h3 className="mb-4 text-lg font-semibold text-ink">Key Metrics</h3>
            <p className="mb-6 text-sm text-muted">
              These are the most important signals that determine the greenwashing risk assessment.
            </p>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <MetricCard
                title="Claims Supported by Evidence"
                value={`${data.supportRatioDetails.percentageSupported.toFixed(0)}%`}
                explanation="What percentage of sustainability targets have linked outcome evidence?"
                interpretation={data.supportRatio >= 1 ? "Most claims are supported" : data.supportRatio >= 0.5 ? "Partial support" : "Most claims lack support"}
                color={data.supportRatio >= 1 ? 'green' : data.supportRatio >= 0.5 ? 'amber' : 'red'}
                icon="📊"
              />
              <MetricCard
                title="Claim Intensity"
                value={`${data.claimPressure}/100`}
                explanation="How strongly the report promotes environmental commitments and future targets."
                interpretation={data.claimPressure > 60 ? "High promotional language" : data.claimPressure > 30 ? "Moderate claims" : "Limited claims"}
                color={data.claimPressure > 60 ? 'red' : data.claimPressure > 30 ? 'amber' : 'green'}
                icon="📢"
              />
              <MetricCard
                title="Evidence Strength"
                value={`${data.outcomeEvidence}/100`}
                explanation="Actual past environmental performance with quantified results."
                interpretation={data.outcomeEvidence > 60 ? "Strong evidence" : data.outcomeEvidence > 30 ? "Moderate evidence" : "Limited evidence"}
                color={data.outcomeEvidence > 60 ? 'green' : data.outcomeEvidence > 30 ? 'amber' : 'red'}
                icon="✅"
              />
            </div>
          </div>

          {/* SECTION 3: Why This Decision? */}
          <div>
            <h3 className="mb-4 text-lg font-semibold text-ink">Why This Decision?</h3>
            <p className="mb-6 text-sm text-muted">
              The system combines multiple signals to assess greenwashing risk. Here's how each factor contributed.
            </p>
            <div className="space-y-4">
              <div className="rounded-xl border border-line bg-white/40 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <p className="font-semibold text-ink">Claim vs. Evidence Gap</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${riskTone === 'red' ? 'bg-red-100 text-red-800' : riskTone === 'amber' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                    {data.greenwashingGap} points
                  </span>
                </div>
                <ProgressBar value={data.greenwashingGap} max={100} color={riskTone} />
                <p className="mt-3 text-sm text-muted">
                  {data.claimPressure > data.outcomeEvidence 
                    ? `Claim intensity (${data.claimPressure}/100) exceeds evidence strength (${data.outcomeEvidence}/100) by ${data.greenwashingGap} points.`
                    : `Evidence strength (${data.outcomeEvidence}/100) meets or exceeds claim intensity (${data.claimPressure}/100).`
                  }
                </p>
              </div>

              <div className="rounded-xl border border-line bg-white/40 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <p className="font-semibold text-ink">Target Support</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${data.supportRatio >= 1 ? 'bg-green-100 text-green-800' : data.supportRatio >= 0.5 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'}`}>
                    {data.supportRatioDetails.percentageSupported.toFixed(0)}% supported
                  </span>
                </div>
                <ProgressBar value={data.supportRatioDetails.percentageSupported} max={100} color={data.supportRatio >= 1 ? 'green' : data.supportRatio >= 0.5 ? 'amber' : 'red'} />
                <p className="mt-3 text-sm text-muted">
                  {data.supportRatioDetails.supportedTargets} of {data.supportRatioDetails.totalTargets} targets have linked outcome evidence.
                </p>
              </div>

              <div className="rounded-xl border border-line bg-white/40 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <p className="font-semibold text-ink">Future Target Density</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${data.futureTargetDensity > 50 ? 'bg-red-100 text-red-800' : data.futureTargetDensity > 25 ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                    {data.futureTargetDensity}/100
                  </span>
                </div>
                <ProgressBar value={data.futureTargetDensity} max={100} color={data.futureTargetDensity > 50 ? 'red' : data.futureTargetDensity > 25 ? 'amber' : 'green'} />
                <p className="mt-3 text-sm text-muted">
                  {data.futureTargetDensity > 50 ? "Many future targets without current achievement data." : "Balanced mix of future targets and current performance."}
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 4: Detected Claims */}
          <div>
            <h3 className="mb-4 text-lg font-semibold text-ink">What Environmental Themes Were Detected?</h3>
            <p className="mb-6 text-sm text-muted">
              The system identified these sustainability topics mentioned in the report.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="card-qml p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Main Environmental Themes</p>
                <ul className="mt-4 space-y-2 text-sm text-ink">
                  {Object.entries(data.indicators.claimLanguage).slice(0, 5).map(([theme, count]) => (
                    <li key={theme} className="flex items-center justify-between">
                      <span>{theme}</span>
                      <span className="font-mono text-xs opacity-75">{count}</span>
                    </li>
                  ))}
                  {Object.keys(data.indicators.claimLanguage).length === 0 && (
                    <li className="text-muted">No notable themes detected</li>
                  )}
                </ul>
              </div>
              <div className="card-qml p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Future Commitments</p>
                <p className="mt-4 text-2xl font-semibold text-ink">{data.outcomeBreakdown.targetSentences}</p>
                <p className="mt-2 text-sm text-muted">
                  Sentences expressing future goals, targets, or commitments.
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 5: Evidence */}
          <div>
            <h3 className="mb-4 text-lg font-semibold text-ink">What Measurable Evidence Was Found?</h3>
            <p className="mb-6 text-sm text-muted">
              These are the actual past performance indicators and quantified results detected.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="card-qml p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Performance Indicators</p>
                <ul className="mt-4 space-y-2 text-sm text-ink">
                  {Object.entries(data.indicators.outcome).slice(0, 5).map(([indicator, count]) => (
                    <li key={indicator} className="flex items-center justify-between">
                      <span>{indicator}</span>
                      <span className="font-mono text-xs opacity-75">{count}</span>
                    </li>
                  ))}
                  {Object.keys(data.indicators.outcome).length === 0 && (
                    <li className="text-muted">No measurable outcomes detected</li>
                  )}
                </ul>
              </div>
              <div className="card-qml p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Quantified Results</p>
                <p className="mt-4 text-2xl font-semibold text-ink">{data.outcomeBreakdown.quantifiedOutcomes}</p>
                <p className="mt-2 text-sm text-muted">
                  Outcomes with specific numbers, metrics, or data points.
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 6: Technical Analysis (Collapsible) */}
          <CollapsibleSection title="Technical Analysis" defaultOpen={false}>
            <div className="space-y-6">
              <div>
                <h4 className="mb-3 font-semibold text-ink">Detailed Metrics</h4>
                <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                  <SmallMetric
                    label="Document Type"
                    value={data.documentType}
                    explanation="Classifies ESG reports, marketing pages, press releases, or unknown content."
                  />
                  <SmallMetric
                    label="Transparency Score"
                    value={data.transparencyScore}
                    suffix="/100"
                    explanation="Framework, assurance, and reporting boundary signals. Informational only."
                  />
                  <SmallMetric
                    label="Confidence Score"
                    value={data.confidenceScore}
                    suffix="/100"
                    explanation="Analysis quality based on signal coverage, linkage quality, and document completeness."
                  />
                  <SmallMetric
                    label="Outcome Sentences"
                    value={data.outcomeBreakdown.outcomeCount}
                    explanation="Sentences classified as past environmental performance, excluding future targets."
                  />
                  <SmallMetric
                    label="Strong Achievements"
                    value={data.outcomeBreakdown.strongAchievements}
                    explanation="Outcomes with strong achievement language (exceeded, certified, etc.)."
                  />
                  <SmallMetric
                    label="Controversy Language"
                    value={data.controversyCount ? data.controversyCount : 'Not Detected'}
                    muted={!data.controversyCount}
                    explanation="Controversy or compliance language detected within this document only. External sources not analyzed."
                  />
                </div>
              </div>

              <div>
                <h4 className="mb-3 font-semibold text-ink">Target-Outcome Linkage Details</h4>
                <div className="card-qml p-5">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted">Total Targets</p>
                      <p className="mt-1 text-lg font-semibold text-ink">{data.supportRatioDetails.totalTargets}</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted">Supported</p>
                      <p className="mt-1 text-lg font-semibold text-green-600">{data.supportRatioDetails.supportedTargets}</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted">Unsupported</p>
                      <p className="mt-1 text-lg font-semibold text-red-600">{data.supportRatioDetails.unsupportedTargets}</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted">% Supported</p>
                      <p className="mt-1 text-lg font-semibold text-ink">{data.supportRatioDetails.percentageSupported.toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted">Avg Match Score</p>
                      <p className="mt-1 text-lg font-semibold text-ink">{data.supportRatioDetails.averageMatchScore.toFixed(3)}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="mb-3 font-semibold text-ink">Risk Drivers</h4>
                <div className="card-qml p-5">
                  <ul className="space-y-2 text-sm text-muted">
                    {data.drivers.risk.map((driver, index) => (
                      <li key={index}>• {driver}</li>
                    ))}
                    {data.drivers.risk.length === 0 && <li>No material risk drivers detected.</li>}
                  </ul>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="card-qml p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">Transparency Signals</p>
                  <ul className="mt-4 space-y-2 text-sm text-ink">
                    {Object.entries(data.indicators.transparency).slice(0, 5).map(([signal, count]) => (
                      <li key={signal}>• {signal} ({count})</li>
                    ))}
                    {Object.keys(data.indicators.transparency).length === 0 && (
                      <li className="text-muted">No transparency signals detected</li>
                    )}
                  </ul>
                </div>
                <div className="card-qml p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">Controversy Signals</p>
                  <ul className="mt-4 space-y-2 text-sm text-ink">
                    {Object.entries(data.controversyHits).slice(0, 5).map(([signal, count]) => (
                      <li key={signal}>• {signal} ({count})</li>
                    ))}
                    {Object.keys(data.controversyHits).length === 0 && (
                      <li className="text-muted">No controversy signals detected</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </CollapsibleSection>

        </div>
      </section>
    </div>
  )
}

export default ResultsPage
