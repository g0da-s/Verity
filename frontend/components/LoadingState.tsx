"use client";

import { useEffect, useState } from "react";

const AGENT_STAGES = [
  { emoji: "🔍", name: "Searching", description: "Finding relevant studies on PubMed" },
  { emoji: "⚖️", name: "Evaluating", description: "Scoring study quality and relevance" },
  { emoji: "✍️", name: "Synthesizing", description: "Generating evidence-based verdict" },
];

type LoadingStateProps = {
  claim: string;
};

export default function LoadingState({ claim }: LoadingStateProps) {
  const [currentStage, setCurrentStage] = useState(0);
  const [dots, setDots] = useState("");

  useEffect(() => {
    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    // Progress through stages
    const stageInterval = setInterval(() => {
      setCurrentStage((prev) => Math.min(prev + 1, AGENT_STAGES.length - 1));
    }, 3000);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(stageInterval);
    };
  }, []);

  return (
    <div className="w-full max-w-lg text-center">
      {/* Claim being analyzed */}
      <div className="mb-10">
        <p className="text-slate-500 text-sm mb-2">Analyzing</p>
        <p className="text-xl font-medium text-slate-700">&quot;{claim}&quot;</p>
      </div>

      {/* Current Stage - Large */}
      <div className="mb-10">
        <div className="text-7xl mb-4 animate-pulse-slow">
          {AGENT_STAGES[currentStage].emoji}
        </div>
        <h2 className="text-2xl font-bold text-slate-800 mb-2">
          {AGENT_STAGES[currentStage].name}{dots}
        </h2>
        <p className="text-slate-500">
          {AGENT_STAGES[currentStage].description}
        </p>
      </div>

      {/* Progress Dots */}
      <div className="flex justify-center gap-3 mb-8">
        {AGENT_STAGES.map((_, index) => (
          <div
            key={index}
            className={`w-3 h-3 rounded-full transition-all duration-500 ${
              index <= currentStage
                ? "bg-blue-500 scale-110"
                : "bg-slate-200"
            }`}
          />
        ))}
      </div>

      <p className="text-sm text-slate-400">
        This usually takes 5-10 seconds
      </p>
    </div>
  );
}
