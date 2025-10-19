// API utility functions for the TTS service

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export interface TTSRequest {
  text: string
  voice_id?: string
}

export async function generateSpeech(text: string, apiKey: string): Promise<ArrayBuffer> {
  const response = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({ text })
  })

  if (!response.ok) {
    throw new Error(`Failed to generate speech: ${response.status} ${response.statusText}`)
  }

  return await response.arrayBuffer()
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`)
    return response.ok
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}