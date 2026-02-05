"use client";

import { useEffect, useState } from "react";

const SCIENCE_FACTS = [
  "Meta-analyses combine data from multiple studies to identify patterns",
  "PubMed contains over 36 million scientific articles",
  "Quality scores consider sample size, study design, and recency",
  "Systematic reviews are considered the gold standard of evidence",
  "Randomized controlled trials (RCTs) minimize bias in research",
  "Claude analyzes study methodology to assess reliability",
];

const AGENT_STAGES = [
  { emoji: "🔍", name: "Search Agent", action: "Finding relevant studies..." },
  { emoji: "⚖️", name: "Quality Evaluator", action: "Scoring evidence..." },
  { emoji: "✍️", name: "Synthesis Agent", action: "Generating verdict..." },
];

export default function LoadingState() {
  const [currentFact, setCurrentFact] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Rotate facts every 4 seconds
    const factInterval = setInterval(() => {
      setCurrentFact((prev) => (prev + 1) % SCIENCE_FACTS.length);
    }, 4000);

    // Progress through stages (simulated)
    const stageInterval = setInterval(() => {
      setCurrentStage((prev) => Math.min(prev + 1, AGENT_STAGES.length - 1));
    }, 10000); // 10s per stage

    // Smooth progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 1, 95)); // Stop at 95% until real completion
    }, 500);

    return () => {
      clearInterval(factInterval);
      clearInterval(stageInterval);
      clearInterval(progressInterval);
    };
  }, []);

  return (
    <div className="mt-8 bg-white rounded-2xl shadow-lg p-8 border border-emerald-100">
      {/* Title */}
      <h3 className="text-xl font-bold text-gray-800 mb-6 text-center">
        Analyzing Evidence...
      </h3>

      {/* Agent Journey - Visual Progress */}
      <div className="flex items-center justify-between mb-8 px-4">
        {AGENT_STAGES.map((agent, index) => (
          <div key={agent.name} className="flex flex-col items-center flex-1">
            {/* Agent Icon */}
            <div
              className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl transition-all duration-500 ${
                index <= currentStage
                  ? "bg-gradient-to-br from-emerald-500 to-teal-500 scale-110"
                  : "bg-gray-100"
              }`}
            >
              <span
                className={`${
                  index <= currentStage ? "animate-bounce" : "opacity-30"
                }`}
              >
                {agent.emoji}
              </span>
            </div>

            {/* Agent Name */}
            <p
              className={`mt-2 text-sm font-medium ${
                index <= currentStage ? "text-emerald-600" : "text-gray-400"
              }`}
            >
              {agent.name}
            </p>

            {/* Connection Line */}
            {index < AGENT_STAGES.length - 1 && (
              <div className="absolute w-1/4 h-0.5 bg-gray-200 top-8 left-1/3 transform -translate-y-1/2 -z-10">
                <div
                  className={`h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500 ${
                    index < currentStage ? "w-full" : "w-0"
                  }`}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Current Action */}
      <div className="text-center mb-6">
        <p className="text-lg text-gray-700 font-medium">
          {AGENT_STAGES[currentStage].action}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Educational Fact */}
      <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-100">
        <p className="text-sm text-emerald-800 flex items-start">
          <span className="mr-2 text-lg">💡</span>
          <span className="flex-1">
            <strong>Did you know?</strong> {SCIENCE_FACTS[currentFact]}
          </span>
        </p>
      </div>

      {/* Estimated Time */}
      <p className="text-center text-sm text-gray-500 mt-6">
        This usually takes 30-60 seconds
      </p>
    </div>
  );
}
