import { useRef, useState } from 'react'
import { parseFiles } from '../utils/fileParsers'

function formatSize(size) {
  if (!size) return '0 KB'
  return `${Math.max(1, Math.round(size / 1024))} KB`
}

function FileUploader({ parsedFiles, onFilesParsed }) {
  const inputRef = useRef(null)
  const [isParsing, setIsParsing] = useState(false)
  const [error, setError] = useState('')

  const handleFiles = async (files) => {
    if (!files?.length) return
    setIsParsing(true)
    setError('')

    try {
      const parsed = await parseFiles(files)
      onFilesParsed(parsed)
    } catch (parseError) {
      setError(parseError.message || 'Unable to parse the selected files.')
    } finally {
      setIsParsing(false)
    }
  }

  return (
    <div className="card-qml">
      <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted">2. File Depositories</p>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault()
          handleFiles(event.dataTransfer.files)
        }}
        className="w-full cursor-pointer rounded-xl border-2 border-dashed border-line bg-background p-10 text-center transition-all hover:bg-[#FCFAF7]"
      >
        <span className="mb-2 block text-3xl">📁</span>
        <p className="text-sm font-semibold text-ink">
          {isParsing ? 'Extracting text from document...' : 'Upload sustainability reports'}
        </p>
        <p className="mt-1 text-xs text-muted">
          Accepts PDF, DOCX, and TXT formats (ESG reports, sustainability disclosures, annual reports)
        </p>
        <span className="mt-4 inline-flex items-center rounded-full border border-line bg-white px-4 py-2 text-xs font-semibold uppercase tracking-wider text-ink transition-all hover:border-muted">
          Browse Storage
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />

      {error ? <p className="mt-3 text-sm font-medium text-rose-600">{error}</p> : null}

      {parsedFiles.length > 0 ? (
        <div className="mt-5 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">Upload Success</p>
          {parsedFiles.map((file) => (
            <div key={`${file.name}-${file.size}`} className="flex items-center justify-between border-b border-line pb-2 text-xs">
              <span className="font-medium text-ink">{file.name}</span>
              <span className="font-mono text-muted">{formatSize(file.size)}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export default FileUploader
