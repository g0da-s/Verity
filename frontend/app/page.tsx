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

type AppState = "idle" | "loading" | "results" | "error" | "validation_error";

type ValidationError = {
  message: string;
  suggestions: string[];
};

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<ValidationError | null>(null);
  const [currentClaim, setCurrentClaim] = useState<string>("");

  const handleSubmit = async (claim: string) => {
    setState("loading");
    setError(null);
    setValidationError(null);
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
        const errorData = await response.json();

        // Handle validation error (400) with suggestions
        if (response.status === 400 && errorData.detail?.suggestions) {
          setValidationError({
            message: errorData.detail.message,
            suggestions: errorData.detail.suggestions,
          });
          setState("validation_error");
          return;
        }

        throw new Error(errorData.detail?.message || `HTTP error! status: ${response.status}`);
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
    setValidationError(null);
    setCurrentClaim("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSubmit(suggestion);
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

      {/* Validation Error State - Claim too vague */}
      {state === "validation_error" && validationError && (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 animate-fadeIn">
          <div className="max-w-lg w-full text-center">
            <div className="text-5xl mb-6">🔍</div>
            <h2 className="text-2xl font-bold text-slate-800 mb-3">
              Be more specific
            </h2>
            <p className="text-slate-600 mb-8">
              {validationError.message}
            </p>

            {validationError.suggestions.length > 0 && (
              <div className="mb-8">
                <p className="text-sm text-slate-500 mb-4">Try one of these:</p>
                <div className="flex flex-col gap-3">
                  {validationError.suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-6 py-3 bg-white text-slate-700 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all text-left shadow-sm hover:shadow-md"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleReset}
              className="text-slate-500 hover:text-blue-600 transition-colors font-medium"
            >
              ← Start over
            </button>
          </div>
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
          Powered by PubMed & Groq AI
        </footer>
      )}
    </main>
  );
}
