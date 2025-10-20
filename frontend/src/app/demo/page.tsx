'use client';

import { useState } from 'react';
import AudioPlayer from '../../components/AudioPlayer';

export default function DemoPage() {
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const synthesizeSpeech = async () => {
    if (!text.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setAudioUrl(null);
    
    try {
      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'test-key', // Demo key for testing
        },
        body: JSON.stringify({ text }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setAudioUrl(audioUrl);
    } catch (err) {
      setError('Failed to synthesize speech. Please try again.');
      console.error('Synthesis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
            ODIADEV-TTS Demo
          </h1>
          <p className="text-xl text-gray-600">
            Experience AI-powered text-to-speech in your own voice
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <div className="mb-6">
            <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
              Enter text to synthesize
            </label>
            <textarea
              id="text"
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
              placeholder="Type your text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <button
            onClick={synthesizeSpeech}
            disabled={isLoading || !text.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Synthesizing...
              </span>
            ) : (
              'Generate Speech'
            )}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}
        </div>

        {audioUrl && (
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Generated Audio</h2>
            <AudioPlayer audioUrl={audioUrl} />
            <div className="mt-4 text-sm text-gray-500">
              <p>Audio generated successfully! This demo showcases the core TTS functionality.</p>
            </div>
          </div>
        )}

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-indigo-600 mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">24/7 Call Coverage</h3>
            <p className="text-gray-600">Never miss a customer call with our AI receptionist that answers in your own voice.</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-indigo-600 mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">WhatsApp Follow-up</h3>
            <p className="text-gray-600">Automatically send personalized voice messages to customers via WhatsApp.</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-indigo-600 mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Missed-call Recovery</h3>
            <p className="text-gray-600">Convert missed calls into voice messages that feel like personal conversations.</p>
          </div>
        </div>

        <div className="mt-12 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Pricing</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Free</h3>
              <div className="text-3xl font-bold text-indigo-600 mb-4">$0<span className="text-lg font-normal text-gray-500">/mo</span></div>
              <ul className="text-left text-gray-600 mb-6 space-y-2">
                <li>• 20 req/day</li>
                <li>• Watermark included</li>
                <li>• Queue lane access</li>
              </ul>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition">
                Get Started
              </button>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-2 border-indigo-500 relative">
              <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
                POPULAR
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Pro</h3>
              <div className="text-3xl font-bold text-indigo-600 mb-4">$49<span className="text-lg font-normal text-gray-500">/mo</span></div>
              <ul className="text-left text-gray-600 mb-6 space-y-2">
                <li>• 50k chars/mo</li>
                <li>• 1 custom voice</li>
                <li>• No watermark</li>
                <li>• Priority lane</li>
              </ul>
              <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition">
                Start Free Trial
              </button>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Business</h3>
              <div className="text-3xl font-bold text-indigo-600 mb-4">$199<span className="text-lg font-normal text-gray-500">/mo</span></div>
              <ul className="text-left text-gray-600 mb-6 space-y-2">
                <li>• 500k chars/mo</li>
                <li>• 3 custom voices</li>
                <li>• No watermark</li>
                <li>• Priority lane</li>
                <li>• Team access</li>
              </ul>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition">
                Contact Sales
              </button>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Enterprise</h3>
              <div className="text-3xl font-bold text-indigo-600 mb-4">Custom</div>
              <ul className="text-left text-gray-600 mb-6 space-y-2">
                <li>• Unlimited usage</li>
                <li>• Unlimited voices</li>
                <li>• No watermark</li>
                <li>• Dedicated lane</li>
                <li>• DPA & SSO</li>
                <li>• SLA guarantee</li>
              </ul>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition">
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}