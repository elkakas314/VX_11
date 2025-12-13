/**
 * Structured Explanation — Render decision tree + alternatives from Madre
 * WS: madre.explanation_structured
 * Fallback: plain text
 */

import React, { useState } from "react";
import { MadreExplanationStructured } from "../../types/v8_1_extensions";

interface StructuredExplanationProps {
    explanation?: MadreExplanationStructured | null;
    plainText?: string;
}

export const StructuredExplanation: React.FC<StructuredExplanationProps> = ({
    explanation,
    plainText = "No explanation available",
}) => {
    const [expandedAlternative, setExpandedAlternative] = useState<number | null>(null);

    if (!explanation) {
        return (
            <div className="p-3 bg-gray-50 rounded border text-sm text-gray-600">
                {plainText}
            </div>
        );
    }

    const { decision_tree, alternatives, confidence } = explanation;

    return (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-300">
            <div className="text-sm font-semibold mb-3">📋 Decision Analysis</div>

            {/* Decision Tree */}
            <div className="p-3 bg-white rounded border border-blue-200">
                <div className="font-semibold text-sm mb-2">Decision: {decision_tree.decision}</div>
                <div className="text-xs text-gray-700 mb-2">{decision_tree.reasoning}</div>
                <div className="text-xs space-y-1">
                    {decision_tree.path.map((p) => (
                        <div key={p.step} className="text-gray-600">
                            <span className="font-mono text-blue-600">→</span> Step {p.step}: {p.action}
                        </div>
                    ))}
                </div>
            </div>

            {/* Confidence Meter */}
            <div className="p-3 bg-white rounded border border-blue-200">
                <div className="text-xs font-semibold mb-2">Confidence: {(confidence * 100).toFixed(1)}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-green-600 h-2 rounded-full transition-all"
                        style={{ width: `${confidence * 100}%` }}
                    />
                </div>
            </div>

            {/* Alternatives */}
            {alternatives && alternatives.length > 0 && (
                <div className="p-3 bg-white rounded border border-blue-200 space-y-2">
                    <div className="text-xs font-semibold">Alternatives:</div>
                    {alternatives.map((alt, idx) => (
                        <div key={idx} className="border-l-2 border-blue-300 pl-2">
                            <button
                                onClick={() => setExpandedAlternative(expandedAlternative === idx ? null : idx)}
                                className="text-xs font-semibold text-blue-700 hover:underline text-left w-full flex justify-between"
                            >
                                <span>{alt.option}</span>
                                <span className="text-gray-500">
                                    {alt.confidence > 0 ? `(${(alt.confidence * 100).toFixed(0)}%)` : ""}
                                </span>
                            </button>

                            {expandedAlternative === idx && (
                                <div className="mt-2 text-xs space-y-1 text-gray-700">
                                    <div>
                                        <span className="font-semibold text-green-700">Pros:</span>{" "}
                                        {alt.pros.join(", ")}
                                    </div>
                                    <div>
                                        <span className="font-semibold text-red-700">Cons:</span> {alt.cons.join(", ")}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
