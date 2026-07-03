function AboutPage() {
  return (
    <div className="page-section">
      <section className="qml-grid relative border-b border-line py-16 md:py-20">
        <div className="container-qml">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
            System Architecture
          </p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-tight text-ink md:text-7xl">
            Platform Methodology & Mission
          </h1>
        </div>
      </section>

      <section className="py-16 md:py-20">
        <div className="container-qml">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-12">

            <div className="space-y-16 lg:col-span-12 max-w-5xl">
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <span className="h-1.5 w-1.5 rounded-full bg-ink" />
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted">
                    Section 01 / Mission
                  </span>
                </div>
                <h2 className="text-4xl font-semibold tracking-tight text-ink">
                  Combating the Greenwashing Ephemera.
                </h2>
                <div className="space-y-4 text-base font-normal leading-8 text-muted">
                  <p>
                    Greenwashing has mutated from a minor public relations gimmick into a systemic
                    corporate shield. Under the guise of ESG statements and vague net-zero promises,
                    multi-national organizations hide continuous environmental exploitation while
                    harvesting institutional capital.
                  </p>
                  <p>
                    Our mission is to <strong>open eyes and strip away the marketing facade</strong>.
                    By automating verification systems and tracking performance claims against concrete
                    reality, we aim to build a zero-tolerance culture for structural corporate deception.
                    Let's make greenwashing unprofitable.
                  </p>
                </div>
              </div>

              <div className="space-y-6 border-t border-line pt-12">
                <div className="flex items-center gap-3">
                  <span className="h-1.5 w-1.5 rounded-full bg-ink" />
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted">
                    Section 02 / Methodology
                  </span>
                </div>
                <h2 className="text-4xl font-semibold tracking-tight text-ink">
                  Document-Driven Claim-Evidence Model.
                </h2>
                <div className="space-y-6 text-base leading-8 text-muted">
                  <p>
                    Instead of asking users for a reported ESG score, the engine reads uploaded documents
                    directly and compares sustainability claim intensity with measurable evidence support:
                  </p>
                  <div className="space-y-2 rounded-xl border border-line bg-cardBg p-6 font-mono text-sm text-ink">
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">
                      // Greenwashing Risk Core Logic
                    </div>
                    <div>Risk = f(Claim_Signal, Evidence_Signal, Transparency_Gap, Controversy_Exposure)</div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-ink">Key Detection Indicators:</h3>
                    <ul className="list-disc space-y-3 pl-5 text-sm">
                      <li>
                        <strong className="text-ink">Greenwashing Gap:</strong> Measures the distance
                        between sustainability claim intensity and verifiable evidence. High marketing
                        density with weak evidence increases greenwashing risk.
                      </li>
                      <li>
                        <strong className="text-ink">Supply Chain Provenance:</strong> Evaluates
                        transactional tracking from origin to processing. Gaps in material transport
                        trigger automated governance penalties.
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="space-y-6 border-t border-line pt-12">
                <div className="flex items-center gap-3">
                  <span className="h-1.5 w-1.5 rounded-full bg-ink" />
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted">
                    Section 03 / Data Ingestion
                  </span>
                </div>
                <h2 className="text-4xl font-semibold tracking-tight text-ink">Multi-source Input Vectors.</h2>
                <p className="text-base leading-8 text-muted">
                  Our platform ingests unstructured corporate documents, regulatory filings (SEC
                  declarations), news articles, and local satellite telemetry data to detect inconsistencies
                  across public messaging.
                </p>
              </div>

              <div className="space-y-6 border-t border-line pt-12">
                <div className="flex items-center gap-3">
                  <span className="h-1.5 w-1.5 rounded-full bg-rose-600" />
                  <span className="text-xs font-semibold uppercase tracking-widest text-rose-600">
                    Section 04 / Constraints & Ethics
                  </span>
                </div>
                <h2 className="text-4xl font-semibold tracking-tight text-ink">Uncertainty & Boundaries.</h2>
                <div className="space-y-4 text-base leading-8 text-muted">
                  <p>
                    Greenwashing outcomes are structurally bound to the availability and relevance of
                    imported files. The software does not operate as an absolute, definitive truth engine,
                    but rather as an interpretable claim-evidence screening device.
                  </p>
                  <p>
                    We enforce transparent calculation loops: any modification vector must correspond to a
                    traceable and verifiable audit log. Our system avoids opaque algorithms to prevent bias
                    towards target companies.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default AboutPage
