import FileUploader from './FileUploader'

function InputPage({
  companyName,
  parsedFiles,
  isProcessing,
  error,
  onCompanyNameChange,
  onFilesParsed,
  onAnalyze,
}) {
  return (
    <div className="page-section">
      <section className="border-b border-line py-20 md:py-24">
        <div className="container-qml">
          <div className="mb-12 max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">ANALYZER</p>
            <h1 className="text-4xl font-semibold tracking-tight text-ink sm:text-6xl">
              Input Ingestion Portal
            </h1>
            <p className="mt-4 text-lg text-muted">
              Upload sustainability reports and let the engine compare claim intensity against verifiable evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
            <div className="space-y-6 lg:col-span-8">
              <div className="card-qml">
                <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted">
                  1. Entity Parameters
                </p>
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label htmlFor="company-name" className="mb-2 block text-xs font-semibold uppercase tracking-wider text-ink">
                      Company Name
                    </label>
                    <input
                      id="company-name"
                      type="text"
                      value={companyName}
                      onChange={(event) => onCompanyNameChange(event.target.value)}
                      placeholder="e.g. Acme Corporation"
                      className="w-full rounded-lg border border-line bg-[#FCFAF7] px-4 py-2.5 text-sm text-ink transition-colors focus:border-muted focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <FileUploader parsedFiles={parsedFiles} onFilesParsed={onFilesParsed} />
            </div>

            <div className="lg:col-span-4">
              <div className="card-qml sticky top-24 space-y-6">
                <p className="text-xs font-semibold uppercase tracking-widest text-muted">3. Analysis Contexts</p>

                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-line pb-2">
                    <span className="text-muted">Claim Signal</span>
                    <span className="font-semibold text-ink">Narrative Density</span>
                  </div>
                  <div className="flex justify-between border-b border-line pb-2">
                    <span className="text-muted">Evidence Signal</span>
                    <span className="font-semibold text-ink">Verifiable Support</span>
                  </div>
                  <div className="flex justify-between border-b border-line pb-2">
                    <span className="text-muted">Risk Model</span>
                    <span className="font-semibold text-ink">Gap + Transparency</span>
                  </div>
                  <p className="leading-5 text-muted">
                    No ESG score input is required. The system reads uploaded reports and compares
                    sustainability claims against measurable evidence.
                  </p>
                </div>

                {error ? <p className="text-sm font-medium leading-6 text-rose-600">{error}</p> : null}

                <div className="border-t border-line pt-4">
                  <button
                    type="button"
                    onClick={async () => {
                      await onAnalyze({
                        companyName,
                        parsedFiles,
                      })
                    }}
                    disabled={isProcessing}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-ink py-3 text-sm font-medium text-white transition-all hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isProcessing ? 'Analyzing Claim-Evidence Gap...' : 'Execute Greenwashing Check'}
                    <span className={isProcessing ? 'h-2 w-2 animate-ping rounded-full bg-white' : ''}>
                      {isProcessing ? '' : '→'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default InputPage
