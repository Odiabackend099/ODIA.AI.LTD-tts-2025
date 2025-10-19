'use client'

import React, { useRef, useEffect } from 'react'

interface AudioPlayerProps {
  audioUrl: string
}

export default function AudioPlayer({ audioUrl }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.load()
      audioRef.current.play().catch(e => console.log("Auto-play prevented:", e))
    }
  }, [audioUrl])

  return (
    <div className="mt-4">
      <audio 
        ref={audioRef} 
        controls 
        className="w-full"
        src={audioUrl}
      >
        Your browser does not support the audio element.
      </audio>
    </div>
  )
}