import { useState } from 'react'

function ContactPage() {
  const [submitted, setSubmitted] = useState(false)

  return (
    <div className="page-section">
      <section className="border-b border-line py-20 md:py-24">
        <div className="container-qml max-w-2xl">
          <div className="mb-12 text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">Transmission</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
              Collaboration Portal
            </h1>
            <p className="mt-6 text-base text-muted">
              Submit observations, bug traces, or feedback on our claim-evidence weighting system.
            </p>
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault()
              setSubmitted(true)
            }}
            className="card-qml space-y-5"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">
              Analysis Transmission
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-ink">
                  Identifier / Name
                </label>
                <input
                  type="text"
                  placeholder="Jane Doe"
                  className="w-full rounded-lg border border-line bg-[#FCFAF7] px-4 py-2.5 text-sm text-ink transition-all focus:border-muted focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-ink">
                  Communication Origin
                </label>
                <input
                  type="email"
                  placeholder="jane@org.net"
                  className="w-full rounded-lg border border-line bg-[#FCFAF7] px-4 py-2.5 text-sm text-ink transition-all focus:border-muted focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-ink">
                Context Categorization
              </label>
              <select className="w-full rounded-md border border-line bg-[#FCFAF7] px-3 py-2 text-sm text-ink transition-all focus:border-muted focus:outline-none">
                <option>Algorithm weighting feedback</option>
                <option>Platform integration query</option>
                <option>General inquiry</option>
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-ink">
                Message / Packet Payload
              </label>
              <textarea
                rows="6"
                placeholder="Provide raw context details or algorithmic concerns here..."
                className="w-full rounded-lg border border-line bg-[#FCFAF7] px-4 py-2.5 text-sm text-ink transition-all focus:border-muted focus:outline-none"
              />
            </div>

            {submitted ? (
              <p className="text-sm font-medium text-accent">Packet capture simulation successful.</p>
            ) : null}

            <div className="pt-2 text-right">
              <button
                type="submit"
                className="inline-flex items-center justify-center rounded-full bg-ink px-6 py-3 text-sm font-medium text-white transition-all hover:bg-neutral-800"
              >
                Transmit Packet <span className="ml-2">→</span>
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}

export default ContactPage
