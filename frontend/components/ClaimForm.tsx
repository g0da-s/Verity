"use client";

import { useState } from "react";

const EXAMPLE_CLAIMS = [
  "Does creatine improve muscle strength?",
  "Does vitamin C prevent colds?",
  "Is intermittent fasting effective for weight loss?",
  "Does melatonin improve sleep quality?",
  "Does omega-3 reduce inflammation?",
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
    <div className="bg-white rounded-2xl shadow-lg p-8 border border-emerald-100">
      <h2 className="text-2xl font-bold text-gray-800 mb-2">
        Verify a Health Claim
      </h2>
      <p className="text-gray-600 mb-6">
        Enter a health-related claim and we'll analyze scientific evidence from PubMed
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="e.g., Does creatine improve muscle strength?"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none"
            rows={3}
            disabled={isLoading}
            minLength={10}
            maxLength={500}
          />
          <p className="text-sm text-gray-500 mt-1">
            {claim.length}/500 characters (minimum 10)
          </p>
        </div>

        <button
          type="submit"
          disabled={isLoading || claim.trim().length < 10}
          className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-emerald-700 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? "Analyzing..." : "Verify Claim"}
        </button>
      </form>

      {/* Example Claims */}
      <div className="mt-8">
        <p className="text-sm font-medium text-gray-700 mb-3">
          Try an example:
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_CLAIMS.map((example) => (
            <button
              key={example}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="text-sm px-3 py-2 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-emerald-200"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
