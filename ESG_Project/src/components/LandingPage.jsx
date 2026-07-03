function LandingPage({ onNavigate }) {
  return (
    <div className="page-section">
      <section className="border-b border-line py-20 md:py-28">
        <div className="container-qml">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.18em] text-muted">
            Document-Driven Detection Model
          </p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-tight text-ink md:text-7xl">
            Demystifying Corporate ESG Assertions & Greenwashing.
          </h1>
          <p className="mt-6 max-w-[58ch] text-lg leading-8 text-muted md:text-xl">
            Unpack empty promises. Upload corporate sustainability declarations and evaluate their real
            ecological impact using dynamic, cross-referenced evidence ratios.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => onNavigate('input')}
              className="inline-flex items-center rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition-all hover:bg-neutral-800"
            >
              Start Analysis
            </button>
            <button
              type="button"
              onClick={() => onNavigate('about')}
              className="inline-flex items-center rounded-full border border-line bg-white px-6 py-3 text-sm font-medium text-ink transition-all hover:border-muted"
            >
              View Methodology
            </button>
          </div>
        </div>
      </section>

      <section className="py-20 md:py-24">
        <div className="container-qml">
          <div className="mb-12 max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
              System Framework
            </p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight text-ink">
              Three modules, one transparent pipeline.
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <button type="button" className="card-qml cursor-pointer text-left" onClick={() => onNavigate('input')}>
              <h3 className="text-2xl font-semibold tracking-tight text-ink">Ingestion Portal</h3>
              <p className="mt-4 leading-7 text-muted">
                Submit corporate filings, ESG reports, and public marketing statements into our processing
                engine.
              </p>
            </button>
            <button type="button" className="card-qml cursor-pointer text-left" onClick={() => onNavigate('about')}>
              <h3 className="text-2xl font-semibold tracking-tight text-ink">Evidence Pipeline</h3>
              <p className="mt-4 leading-7 text-muted">
                Cross-reference statements with external datasets, independent journalism, and raw supply
                chain metrics.
              </p>
            </button>
            <button type="button" className="card-qml cursor-pointer text-left" onClick={() => onNavigate('results')}>
              <h3 className="text-2xl font-semibold tracking-tight text-ink">Greenwashing Risk</h3>
              <p className="mt-4 leading-7 text-muted">
                Compare claim intensity with verifiable evidence to produce transparent greenwashing risk signals.
              </p>
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

export default LandingPage
