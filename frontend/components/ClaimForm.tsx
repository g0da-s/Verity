"use client";

import { useState } from "react";

const EXAMPLE_CLAIMS = [
  "Does creatine improve muscle strength?",
  "Does vitamin C prevent colds?",
  "Is intermittent fasting effective for weight loss?",
];

type ClaimFormProps = {
  onSubmit: (claim: string) => void;
  isLoading: boolean;
};

export default function ClaimForm({ onSubmit, isLoading }: ClaimFormProps) {
  const [claim, setClaim] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (claim.trim().length >= 10) {
      onSubmit(claim.trim());
    }
  };

  const handleExampleClick = (exampleClaim: string) => {
    setClaim(exampleClaim);
    onSubmit(exampleClaim);
  };

  return (
    <div className="w-full max-w-2xl">
      <form onSubmit={handleSubmit} className="relative">
        {/* Main Input */}
        <div className="relative">
          <input
            type="text"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Enter a health claim to verify..."
            className="w-full px-6 py-5 text-lg text-slate-800 bg-white border-2 border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all placeholder:text-slate-400"
            disabled={isLoading}
            minLength={10}
            maxLength={500}
          />

          {/* Search Button */}
          <button
            type="submit"
            disabled={isLoading || claim.trim().length < 10}
            className="absolute right-3 top-1/2 -translate-y-1/2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-200 disabled:shadow-none"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </span>
            ) : (
              "Verify"
            )}
          </button>
        </div>

        {/* Character Count */}
        <p className="text-sm text-slate-400 mt-3 text-center">
          {claim.length > 0 && `${claim.length}/500`}
          {claim.length > 0 && claim.length < 10 && " (minimum 10 characters)"}
        </p>
      </form>

      {/* Example Claims */}
      <div className="mt-8 text-center">
        <p className="text-sm text-slate-500 mb-4">Try an example:</p>
        <div className="flex flex-wrap justify-center gap-3">
          {EXAMPLE_CLAIMS.map((example) => (
            <button
              key={example}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="text-sm px-4 py-2 bg-white text-slate-600 rounded-full hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all border border-slate-200 shadow-sm"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
