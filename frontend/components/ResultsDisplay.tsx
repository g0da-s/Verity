"use client";

import { VerificationResult } from "@/app/page";

type ResultsDisplayProps = {
  result: VerificationResult;
};

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Verdict Card */}
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 p-8 border border-slate-100">
        {/* Verdict Header */}
        <div className="flex items-start gap-6 mb-6">
          <div className="text-6xl">{result.verdict_emoji}</div>
          <div className="flex-1">
            <p className="text-sm text-slate-500 mb-1">Verdict</p>
            <h1 className="text-3xl font-bold text-slate-800">
              {result.verdict}
            </h1>
          </div>
        </div>

        {/* Original Claim */}
        <div className="bg-slate-50 rounded-xl p-4 mb-6 border border-slate-100">
          <p className="text-sm text-slate-500 mb-1">Your claim</p>
          <p className="text-slate-700 font-medium">&quot;{result.claim}&quot;</p>
        </div>

        {/* Summary */}
        <div
          className="prose prose-slate max-w-none text-slate-600 leading-relaxed text-lg [&>p]:mb-4 [&>strong]:text-slate-800 [&>strong]:font-semibold"
          dangerouslySetInnerHTML={{
            __html: result.summary
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\n/g, '<br />')
              .replace(/• /g, '<br />• ')
          }}
        />

        {/* Stats */}
        <div className="mt-8 grid grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-xl p-4 text-center border border-blue-100">
            <p className="text-3xl font-bold text-blue-600">
              {result.stats.studies_found}
            </p>
            <p className="text-sm text-slate-600 mt-1">Studies Found</p>
          </div>
          <div className="bg-indigo-50 rounded-xl p-4 text-center border border-indigo-100">
            <p className="text-3xl font-bold text-indigo-600">
              {result.stats.studies_scored}
            </p>
            <p className="text-sm text-slate-600 mt-1">Evaluated</p>
          </div>
          <div className="bg-violet-50 rounded-xl p-4 text-center border border-violet-100">
            <p className="text-3xl font-bold text-violet-600">
              {result.stats.top_studies_count}
            </p>
            <p className="text-sm text-slate-600 mt-1">Top Quality</p>
          </div>
        </div>
      </div>

      {/* Supporting Studies */}
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 p-8 border border-slate-100">
        <h2 className="text-xl font-bold text-slate-800 mb-6">
          Supporting Evidence
        </h2>

        <div className="space-y-4">
          {result.top_studies.map((study, index) => (
            <div
              key={study.pubmed_id}
              className="border border-slate-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all bg-slate-50/50"
            >
              {/* Study Header */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-800 leading-tight">
                    {index + 1}. {study.title}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {study.authors} &bull; {study.journal} ({study.year})
                  </p>
                </div>
                {study.quality_score && (
                  <div className="flex-shrink-0">
                    <div className="bg-blue-100 text-blue-700 font-bold px-3 py-1.5 rounded-full text-sm">
                      {study.quality_score.toFixed(1)}/10
                    </div>
                  </div>
                )}
              </div>

              {/* Study Tags */}
              {study.sample_size > 0 && (
                <div className="mb-3">
                  <span className="text-sm text-slate-500">
                    {study.sample_size.toLocaleString()} participants
                  </span>
                </div>
              )}

              {/* PubMed Link */}
              <a
                href={study.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View on PubMed
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Search Queries - Collapsible */}
      <details className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-100 overflow-hidden">
        <summary className="p-6 cursor-pointer hover:bg-slate-50 transition-colors font-semibold text-slate-700">
          Search Queries Used ({result.search_queries.length})
        </summary>
        <div className="px-6 pb-6 space-y-2">
          {result.search_queries.map((query, index) => (
            <div
              key={index}
              className="text-sm text-slate-600 bg-slate-50 rounded-lg px-4 py-3 border border-slate-200 font-mono"
            >
              {query}
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
