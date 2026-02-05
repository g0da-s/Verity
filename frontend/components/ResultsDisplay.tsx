"use client";

import { VerificationResult } from "@/app/page";

type ResultsDisplayProps = {
  result: VerificationResult;
};

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  return (
    <div className="mt-8 space-y-6 animate-fadeIn">
      {/* Verdict Card */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-emerald-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Verdict: {result.verdict}
            </h2>
            <p className="text-gray-600 mb-4">
              Claim: &quot;{result.claim}&quot;
            </p>
          </div>
          <div className="text-6xl">{result.verdict_emoji}</div>
        </div>

        {/* Summary */}
        <div className="mt-6 prose prose-emerald max-w-none">
          <p className="text-gray-700 leading-relaxed whitespace-pre-line">
            {result.summary}
          </p>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-emerald-50 rounded-lg p-4 text-center border border-emerald-100">
            <p className="text-2xl font-bold text-emerald-600">
              {result.stats.studies_found}
            </p>
            <p className="text-sm text-gray-600 mt-1">Studies Found</p>
          </div>
          <div className="bg-teal-50 rounded-lg p-4 text-center border border-teal-100">
            <p className="text-2xl font-bold text-teal-600">
              {result.stats.studies_scored}
            </p>
            <p className="text-sm text-gray-600 mt-1">Studies Scored</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center border border-green-100">
            <p className="text-2xl font-bold text-green-600">
              {result.stats.top_studies_count}
            </p>
            <p className="text-sm text-gray-600 mt-1">Top Quality Studies</p>
          </div>
        </div>
      </div>

      {/* Supporting Studies */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-emerald-100">
        <h3 className="text-xl font-bold text-gray-800 mb-6">
          🔬 Supporting Evidence ({result.top_studies.length} studies)
        </h3>

        <div className="space-y-4">
          {result.top_studies.map((study, index) => (
            <div
              key={study.pubmed_id}
              className="border border-gray-200 rounded-lg p-6 hover:border-emerald-300 hover:shadow-md transition-all"
            >
              {/* Study Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 mb-1">
                    {index + 1}. {study.title}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {study.authors} • {study.journal} ({study.year})
                  </p>
                </div>
                {study.quality_score && (
                  <div className="ml-4 flex-shrink-0">
                    <div className="bg-emerald-100 text-emerald-700 font-bold px-3 py-1 rounded-full text-sm">
                      {study.quality_score.toFixed(1)}/10
                    </div>
                  </div>
                )}
              </div>

              {/* Study Details */}
              <div className="flex flex-wrap gap-3 mb-3">
                <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded border border-blue-200">
                  {study.study_type === 'Meta-Analysis' 
                    ? '📚 Review of Multiple Studies' 
                    : study.study_type === 'Randomized Controlled Trial'
                    ? '🔬 Controlled Experiment'
                    : study.study_type}
                </span>
                <span className="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded border border-purple-200">
                  {study.sample_size > 0 
                    ? `👥 ${study.sample_size.toLocaleString()} people` 
                    : '👥 Sample size not specified'}
                </span>
              </div>

              {/* Link to PubMed */}
              <a
                href={study.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-emerald-600 hover:text-emerald-700 font-medium inline-flex items-center"
              >
                View on PubMed →
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Search Queries Used */}
      <details className="bg-white rounded-2xl shadow-lg border border-emerald-100 overflow-hidden">
        <summary className="p-6 cursor-pointer hover:bg-emerald-50 transition-colors">
          <span className="font-semibold text-gray-800">
            🔎 Search Queries Used ({result.search_queries.length})
          </span>
        </summary>
        <div className="px-6 pb-6 space-y-2">
          {result.search_queries.map((query, index) => (
            <div
              key={index}
              className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2 border border-gray-200"
            >
              {query}
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
