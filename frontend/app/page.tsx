"use client";

import { useState } from "react";
import ClaimForm from "@/components/ClaimForm";
import LoadingState from "@/components/LoadingState";
import ResultsDisplay from "@/components/ResultsDisplay";

export type VerificationResult = {
  claim: string;
  verdict: string;
  verdict_emoji: string;
  summary: string;
  top_studies: Array<{
    pubmed_id: string;
    title: string;
    authors: string;
    journal: string;
    year: number;
    study_type: string;
    sample_size: number;
    url: string;
    quality_score?: number;
    quality_rationale?: string;
  }>;
  search_queries: string[];
  stats: {
    studies_found: number;
    studies_scored: number;
    top_studies_count: number;
  };
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (claim: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/truthcheck/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ claim }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to verify claim");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
            🔬 TruthCheck
          </h1>
          <p className="text-gray-600 mt-1">Science-Backed Health Answers</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Claim Input Form */}
        <ClaimForm onSubmit={handleSubmit} isLoading={loading} />

        {/* Loading State */}
        {loading && <LoadingState />}

        {/* Error State */}
        {error && (
          <div className="mt-8 p-6 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-red-800 font-medium">❌ Error: {error}</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && <ResultsDisplay result={result} />}
      </div>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t border-emerald-100 bg-white/50">
        <div className="max-w-6xl mx-auto px-4 text-center text-gray-600 text-sm">
          <p>Powered by PubMed, Claude Sonnet 4.5, and LangGraph</p>
          <p className="mt-2">Evidence-based health claim verification</p>
        </div>
      </footer>
    </main>
  );
}
