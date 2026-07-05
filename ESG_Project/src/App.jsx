import { useEffect, useState } from 'react'
import AboutPage from './components/AboutPage'
import ContactPage from './components/ContactPage'
import InputPage from './components/InputPage'
import LandingPage from './components/LandingPage'
import Navbar from './components/Navbar'
import ResultsPage from './components/ResultsPage'

function App() {
  const [currentPage, setCurrentPage] = useState('landing')
  const [companyName, setCompanyName] = useState('')
  const [parsedFiles, setParsedFiles] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [currentPage])

  const navigate = (page) => {
    setCurrentPage(page)
  }

  const analyze = async () => {
    if (!companyName.trim()) {
      setError('Enter a company name before running the greenwashing analysis.')
      return
    }

    if (!parsedFiles.length) {
      setError('Upload at least one PDF, TXT, or CSV file before analysis.')
      return
    }

    setError('')
    setIsProcessing(true)

    try {
      const res = await fetch('http://127.0.0.1:8000', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: parsedFiles.map(f => f.text || '').join('\n'),
        }),
      })

      const result = await res.json()

      setAnalysisResult(result)
      setCurrentPage('results')
    } catch (err) {
      setError('Analysis failed. Backend may not be running.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-ink selection:bg-ink selection:text-background">
      <Navbar currentPage={currentPage} onNavigate={navigate} />
      <main className="min-h-screen">
        {currentPage === 'landing' ? <LandingPage onNavigate={navigate} /> : null}
        {currentPage === 'input' ? (
          <InputPage
            companyName={companyName}
            parsedFiles={parsedFiles}
            isProcessing={isProcessing}
            error={error}
            onCompanyNameChange={setCompanyName}
            onFilesParsed={setParsedFiles}
            onAnalyze={analyze}
          />
        ) : null}
        {currentPage === 'results' ? <ResultsPage result={analysisResult} onNavigate={navigate} /> : null}
        {currentPage === 'about' ? <AboutPage /> : null}
        {currentPage === 'contact' ? <ContactPage /> : null}
      </main>
    </div>
  )
}

export default App
