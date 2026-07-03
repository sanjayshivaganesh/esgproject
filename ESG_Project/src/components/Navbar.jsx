function Navbar({ currentPage, onNavigate }) {
  const linkClass = (page) =>
    `text-sm font-medium transition-colors ${
      currentPage === page ? 'text-muted' : 'text-ink hover:text-muted'
    }`

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-background/85 backdrop-blur-md">
      <nav className="container-qml flex items-center justify-between py-5">
        <button
          type="button"
          onClick={() => onNavigate('landing')}
          className="text-left text-sm font-semibold uppercase tracking-[0.18em] text-ink"
        >
          ESG INTEGRITY NEXUS
        </button>
        <div className="flex items-center gap-5 sm:gap-8">
          <button type="button" onClick={() => onNavigate('input')} className={linkClass('input')}>
            Analyze
          </button>
          <button type="button" onClick={() => onNavigate('about')} className={linkClass('about')}>
            Methodology
          </button>
          <button type="button" onClick={() => onNavigate('contact')} className={linkClass('contact')}>
            Feedback
          </button>
        </div>
      </nav>
    </header>
  )
}

export default Navbar
