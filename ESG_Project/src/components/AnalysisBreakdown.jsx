function DriverList({ title, tone, drivers, emptyText }) {
  const toneClass =
    tone === 'risk' ? 'text-rose-600' : tone === 'evidence' ? 'text-emerald-700' : 'text-accent'

  return (
    <div>
      <p className={`mb-3 text-xs font-semibold uppercase tracking-widest ${toneClass}`}>{title}</p>
      <div className="space-y-2">
        {drivers.length ? (
          drivers.map((item) => (
            <div
              key={`${item.category}-${item.label}`}
              className="grid grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-line pb-2 text-xs"
              title={item.explanation}
            >
              <span className="rounded-full border border-line px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-muted">
                {item.category}
              </span>
              <span className="min-w-0 text-muted">{item.label}</span>
              <span className={`whitespace-nowrap font-mono font-semibold ${toneClass}`}>
                {item.value}
              </span>
            </div>
          ))
        ) : (
          <p className="text-xs text-muted">{emptyText}</p>
        )}
      </div>
    </div>
  )
}

function PhraseList({ title, tone, items, emptyText }) {
  const toneClass = tone === 'risk' ? 'text-rose-600' : 'text-accent'

  return (
    <div>
      <p className={`mb-3 text-xs font-semibold uppercase tracking-widest ${toneClass}`}>{title}</p>
      <div className="space-y-2">
        {items.length ? (
          items.slice(0, 6).map((item) => (
            <div key={`${item.phrase}-${item.category || title}`} className="flex justify-between gap-3 border-b border-line pb-2 text-xs">
              <span className="min-w-0 text-muted">{item.phrase}</span>
              <span className="shrink-0 font-mono text-ink">{item.count}</span>
            </div>
          ))
        ) : (
          <p className="text-xs text-muted">{emptyText}</p>
        )}
      </div>
    </div>
  )
}

function AnalysisBreakdown({ result }) {
  const claimDrivers = result.claimComponents ?? []
  const evidenceDrivers = result.evidenceComponents ?? []
  const riskDrivers = []

  const controversyHits = result.controversy?.hits ?? []
  const flaggedPhrases = result.flaggedPhrases ?? []
  const positiveIndicators = result.positiveIndicators ?? []
  const modelConfidence = Number.isFinite(result.confidenceLevel)
    ? Math.round(result.confidenceLevel)
    : 0
  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <div className="card-qml p-6">
        <p className="text-xs font-semibold uppercase tracking-featured-eyebrow text-accent">
          Drivers
        </p>
        <h2 className="mt-4 text-2xl font-semibold tracking-tight text-ink">Score Movement</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Claim intensity, evidence strength, and risk factors are shown separately so climate language is not treated as inherently negative.
        </p>

        <div className="mt-6 grid gap-6">
          <DriverList
            title="Claim Intensity Drivers"
            tone="claim"
            drivers={claimDrivers}
            emptyText="No major claim intensity drivers detected."
          />
          <DriverList
            title="Evidence Strength Drivers"
            tone="evidence"
            drivers={evidenceDrivers}
            emptyText="No major evidence strength drivers detected."
          />
          <DriverList
            title="Risk Drivers"
            tone="risk"
            drivers={riskDrivers}
            emptyText="No material risk drivers detected."
          />
        </div>
      </div>

      <div className="card-qml p-6">
        <p className="text-xs font-semibold uppercase tracking-featured-eyebrow text-accent">
          Controversies
        </p>
        <h2 className="mt-4 text-2xl font-semibold tracking-tight text-ink">Context Signals</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Controversy indicators influence risk as cautionary context, without exposing internal penalty math.
        </p>
        <div className="mt-6">
          <PhraseList
            title="Detected Indicators"
            tone="risk"
            items={controversyHits}
            emptyText="No controversy indicators detected."
          />
        </div>
      </div>

      <div className="card-qml p-6">
        <p className="text-xs font-semibold uppercase tracking-featured-eyebrow text-accent">
          Indicators
        </p>
        <h2 className="mt-4 text-2xl font-semibold tracking-tight text-ink">Signals Found</h2>
        <div className="mt-6 grid gap-5">
          <PhraseList
            title="Flagged Claim Language"
            tone="risk"
            items={flaggedPhrases}
            emptyText="No major claim or controversy phrase clusters detected."
          />
          <PhraseList
            title="Credibility Indicators"
            tone="good"
            items={positiveIndicators}
            emptyText="No strong transparency or metrics language found."
          />
        </div>

        <div className="mt-6 rounded-lg border border-line p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">
            Analysis Confidence
          </p>
          <p className="mt-2 text-2xl font-semibold text-ink">
            {modelConfidence}/100
          </p>
          <p className="mt-2 text-sm text-muted">
            Indicates how confident the model is in its classification based on the available document evidence.
          </p>
        </div>
      </div>
    </div>
  )
}

export default AnalysisBreakdown
