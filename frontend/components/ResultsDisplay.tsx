"use client";

import { VerificationResult } from "@/app/page";

type ResultsDisplayProps = {
  result: VerificationResult;
};

type SummarySection = {
  heading: string;
  content: string;
};

// Strips ** and trailing : from heading text (handles fallback format like "**Bottom Line:**")
function cleanHeading(raw: string): string {
  return raw.replace(/\*\*/g, "").replace(/:$/, "").trim();
}

// Parses "## Heading\ncontent\n## Next Heading\n..." into sections.
// Falls back to splitting on "**Heading:**" if no ## headings are found.
function parseSummary(summary: string): SummarySection[] {
  const sections: SummarySection[] = [];

  // Primary: split on ## headings (what the backend produces)
  const parts = summary.split(/^## /gm);

  if (parts.length > 1) {
    for (const part of parts) {
      const trimmed = part.trim();
      if (!trimmed) continue;

      const newlineIndex = trimmed.indexOf("\n");
      if (newlineIndex === -1) {
        sections.push({ heading: "", content: trimmed });
      } else {
        sections.push({
          heading: cleanHeading(trimmed.slice(0, newlineIndex)),
          content: trimmed.slice(newlineIndex + 1).trim(),
        });
      }
    }
    return sections;
  }

  // Fallback: split on **Heading:** lines
  const boldParts = summary.split(/^(?=\*\*[^*]+\*\*:?)/gm);
  for (const part of boldParts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    const match = trimmed.match(/^\*\*([^*]+)\*\*:?\s*\n?([\s\S]*)/);
    if (match) {
      sections.push({ heading: cleanHeading(match[1]), content: match[2].trim() });
    } else {
      sections.push({ heading: "", content: trimmed });
    }
  }
  return sections;
}

// Escapes raw text so it cannot be interpreted as HTML
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Renders **bold** → <strong>, with all other content escaped
function renderInline(text: string): string {
  // Split on **…** boundaries, escape each segment, then wrap bold ones
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts
    .map((part) => {
      const boldMatch = part.match(/^\*\*(.*)\*\*$/);
      return boldMatch
        ? `<strong>${escapeHtml(boldMatch[1])}</strong>`
        : escapeHtml(part);
    })
    .join("");
}

// Renders a block of content: bullet lines → styled list, plain lines → paragraphs
function renderContent(content: string) {
  const lines = content.split("\n").filter((l) => l.trim());
  const elements: React.ReactNode[] = [];
  let bulletBuffer: string[] = [];

  const flushBullets = () => {
    if (bulletBuffer.length === 0) return;
    elements.push(
      <ul className="space-y-2 mt-2" key={`bullets-${elements.length}`}>
        {bulletBuffer.map((bullet, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5 flex-shrink-0">•</span>
            <span
              className="text-slate-600 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: renderInline(bullet) }}
            />
          </li>
        ))}
      </ul>
    );
    bulletBuffer = [];
  };

  for (const line of lines) {
    if (line.startsWith("•") || line.startsWith("-")) {
      bulletBuffer.push(line.replace(/^[•\-]\s*/, ""));
    } else {
      flushBullets();
      elements.push(
        <p
          key={`p-${elements.length}`}
          className="text-slate-600 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: renderInline(line) }}
        />
      );
    }
  }
  flushBullets();

  return <>{elements}</>;
}

const sectionStyles: Record<
  string,
  { bg: string; border: string; icon: string; headingColor: string }
> = {
  "Bottom Line": {
    bg: "bg-blue-50",
    border: "border-blue-200",
    icon: "💡",
    headingColor: "text-blue-800",
  },
  "What Research Found": {
    bg: "bg-white",
    border: "border-slate-200",
    icon: "🔬",
    headingColor: "text-slate-800",
  },
  "Who Benefits Most": {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    icon: "👤",
    headingColor: "text-emerald-800",
  },
  "Dosage & Timing": {
    bg: "bg-amber-50",
    border: "border-amber-200",
    icon: "💊",
    headingColor: "text-amber-800",
  },
  "Important Caveats": {
    bg: "bg-red-50",
    border: "border-red-200",
    icon: "⚠️",
    headingColor: "text-red-800",
  },
};

const defaultStyle = {
  bg: "bg-white",
  border: "border-slate-200",
  icon: "",
  headingColor: "text-slate-800",
};

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  const sections = parseSummary(result.summary);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Verdict Card */}
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 p-8 border border-slate-100">
        <div className="flex items-start gap-6 mb-6">
          <div className="text-6xl">{result.verdict_emoji}</div>
          <div className="flex-1">
            <p className="text-sm text-slate-500 mb-1">Verdict</p>
            <h1 className="text-3xl font-bold text-slate-800">
              {result.verdict}
            </h1>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p className="text-sm text-slate-500 mb-1">Your claim</p>
          <p className="text-slate-700 font-medium">&quot;{result.claim}&quot;</p>
        </div>
      </div>

      {/* Summary Sections — each ## heading becomes its own card */}
      {sections.map((section, i) => {
        const style = sectionStyles[section.heading] ?? defaultStyle;

        return (
          <div
            key={i}
            className={`${style.bg} rounded-2xl shadow-lg shadow-slate-200/50 p-6 border ${style.border}`}
          >
            {section.heading && (
              <h2
                className={`text-lg font-bold ${style.headingColor} mb-3 flex items-center gap-2`}
              >
                <span>{style.icon}</span>
                {section.heading}
              </h2>
            )}
            {renderContent(section.content)}
          </div>
        );
      })}

      {/* Supporting Studies */}
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 p-8 border border-slate-100">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-800">
            Supporting Evidence
          </h2>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <span>{result.stats.studies_found} found</span>
            <span className="text-slate-300">•</span>
            <span>{result.stats.studies_scored} evaluated</span>
            <span className="text-slate-300">•</span>
            <span>{result.stats.top_studies_count} top quality</span>
          </div>
        </div>

        <div className="space-y-4">
          {result.top_studies.map((study, index) => (
            <div
              key={study.pubmed_id}
              className="border border-slate-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all bg-slate-50/50"
            >
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

              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2.5 py-1 rounded-full">
                  {study.study_type}
                </span>
                {study.sample_size > 0 && (
                  <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2.5 py-1 rounded-full">
                    n={study.sample_size.toLocaleString()}
                  </span>
                )}
                {study.quality_rationale && (
                  <span className="text-xs text-slate-500 italic">
                    {study.quality_rationale}
                  </span>
                )}
              </div>

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
      {result.search_queries.length > 0 && (
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
      )}
    </div>
  );
}
