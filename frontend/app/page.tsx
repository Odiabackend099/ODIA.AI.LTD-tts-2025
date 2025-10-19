'use client'
import { useState } from 'react'
import AudioPlayer from '@/components/AudioPlayer'
import { generateSpeech } from '@/lib/api'

export default function Page() {
  const [text, setText] = useState('')
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    setLoading(true)
    setAudioUrl(null)
    setError(null)
    
    const apiKey = localStorage.getItem('ODIADEV_API_KEY') || ''
    if (!apiKey) {
      setError('API key not found. Please set ODIADEV_API_KEY in localStorage.')
      setLoading(false)
      return
    }
    
    try {
      const arrayBuffer = await generateSpeech(text, apiKey)
      const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error generating speech:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">ODIADEV TTS Demo</h1>
      
      <div className="mb-4">
        <label htmlFor="apiKey" className="block text-sm font-medium mb-1">
          API Key
        </label>
        <input
          type="password"
          id="apiKey"
          className="w-full p-2 border rounded"
          placeholder="Enter your API key"
          onBlur={(e) => localStorage.setItem('ODIADEV_API_KEY', e.target.value)}
          defaultValue={localStorage.getItem('ODIADEV_API_KEY') || ''}
        />
      </div>
      
      <textarea
        className="w-full h-32 p-2 border rounded"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to convert to speech..."
      />
      
      <button
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        onClick={generate}
        disabled={loading || !text.trim()}
      >
        {loading ? 'Generating...' : 'Generate Speech'}
      </button>
      
      {error && (
        <div className="mt-4 p-2 bg-red-100 text-red-700 rounded">
          Error: {error}
        </div>
      )}
      
      {audioUrl && (
        <div className="mt-6">
          <AudioPlayer audioUrl={audioUrl} />
          <a 
            href={audioUrl} 
            download="tts-output.mp3"
            className="mt-2 inline-block px-4 py-2 bg-green-500 text-white rounded"
          >
            Download MP3
          </a>
        </div>
      )}
    </main>
  )
}