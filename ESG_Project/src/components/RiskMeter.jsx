function RiskMeter({ riskScore, riskLevel }) {
  const meterColor =
    riskLevel === 'Low' ? 'bg-accent' : riskLevel === 'Moderate' ? 'bg-yellow-600' : 'bg-rose-600'

  return (
    <div className="card-qml">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-featured-eyebrow text-accent">Risk Meter</p>
        <span className="font-mono text-xs font-semibold text-ink">{riskLevel} Risk</span>
      </div>
      <div className="mt-6 h-2 w-full overflow-hidden rounded-full bg-line">
        <div
          className={`h-full rounded-full ${meterColor} transition-all duration-700 ease-out`}
          style={{ width: `${riskScore}%` }}
        />
      </div>
      <div className="mt-3 flex justify-between font-mono text-[10px] uppercase tracking-widest text-muted">
        <span>0 Low</span>
        <span>31 Moderate</span>
        <span>61 High</span>
      </div>
      <p className="mt-4 text-xs leading-5 text-muted">
        Risk reflects the greenwashing gap between claim pressure and outcome evidence. Transparency only adjusts risk slightly.
      </p>
    </div>
  )
}

export default RiskMeter
