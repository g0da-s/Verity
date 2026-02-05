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

type AppState = "idle" | "loading" | "results" | "error";

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentClaim, setCurrentClaim] = useState<string>("");

  const handleSubmit = async (claim: string) => {
    setState("loading");
    setError(null);
    setResult(null);
    setCurrentClaim(claim);

    try {
      const response = await fetch("http://localhost:8000/api/verity/verify", {
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
      setState("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to verify claim");
      setState("error");
    }
  };

  const handleReset = () => {
    setState("idle");
    setResult(null);
    setError(null);
    setCurrentClaim("");
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Idle State - Centered Search */}
      {state === "idle" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 animate-fadeIn">
          <div className="text-center mb-12">
            <h1 className="text-6xl font-light tracking-tight text-slate-800 mb-3">
              verity
            </h1>
            <div className="w-12 h-1 bg-blue-500 mx-auto mb-4 rounded-full"></div>
            <p className="text-lg text-slate-500 font-light tracking-wide">
              health claims, verified by science
            </p>
          </div>
          <ClaimForm onSubmit={handleSubmit} isLoading={false} />
        </div>
      )}

      {/* Loading State - Replaces Form */}
      {state === "loading" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 animate-fadeIn">
          <LoadingState claim={currentClaim} />
        </div>
      )}

      {/* Error State */}
      {state === "error" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 animate-fadeIn">
          <div className="max-w-md w-full text-center">
            <div className="text-6xl mb-6">😕</div>
            <h2 className="text-2xl font-bold text-slate-800 mb-4">
              Something went wrong
            </h2>
            <p className="text-slate-600 mb-8">{error}</p>
            <button
              onClick={handleReset}
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-full hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results State - Replaces Form */}
      {state === "results" && result && (
        <div className="min-h-screen py-8 px-4 animate-fadeIn">
          <div className="max-w-4xl mx-auto">
            {/* Back Button */}
            <button
              onClick={handleReset}
              className="mb-6 flex items-center gap-2 text-slate-600 hover:text-blue-600 transition-colors font-medium"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              New Search
            </button>

            <ResultsDisplay result={result} />
          </div>
        </div>
      )}

      {/* Subtle Footer - Only on idle */}
      {state === "idle" && (
        <footer className="fixed bottom-0 left-0 right-0 py-4 text-center text-slate-400 text-xs tracking-wide">
          Powered by PubMed & Claude AI
        </footer>
      )}
    </main>
  );
}
