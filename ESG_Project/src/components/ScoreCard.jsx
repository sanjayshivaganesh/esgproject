function ScoreCard({ label, value, suffix = '/ 100', tone = 'muted', description, badge }) {
  const isNumeric = typeof value === 'number'
  const toneClass = {
    muted: 'text-muted',
    risk: 'text-rose-600',
    ink: 'text-ink',
    good: 'text-accent',
  }[tone]

  return (
    <div className={`card-qml flex min-h-56 min-w-0 flex-col justify-between p-6 overflow-hidden ${tone === 'ink' ? 'border-2 border-ink hover:border-ink' : ''}`}>
      <p className={`text-xs font-semibold uppercase tracking-widest ${tone === 'ink' ? 'text-accent' : 'text-muted'}`}>
        {label}
      </p>
      <div className="my-5">
        <span className={`inline-flex max-w-full flex-wrap items-baseline break-words font-bold tracking-tight ${isNumeric ? 'text-3xl md:text-4xl xl:text-5xl' : 'text-3xl md:text-4xl'} ${toneClass}`}>
          <span className="break-all">{value}</span>
          {suffix ? <span className="ml-2 break-words text-base md:text-lg xl:text-xl">{suffix}</span> : null}
        </span>
        {badge ? <span className="ml-2 font-mono text-xs font-semibold text-rose-500">{badge}</span> : null}
      </div>
      <p className={`text-xs leading-5 ${tone === 'ink' ? 'font-semibold text-ink' : 'text-muted'}`}>{description}</p>
    </div>
  )
}

export default ScoreCard
