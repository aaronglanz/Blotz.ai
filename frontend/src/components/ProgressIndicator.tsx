import { useEffect, useRef, useState } from "react";

const PHASES = {
  interpreting: {
    title: "Understanding your lifestyle\u2026",
    steps: [
      { icon: "🧠", text: "Reading your lifestyle description" },
      { icon: "🔍", text: "Extracting what you really want" },
      { icon: "✍️", text: "Refining your search brief" },
    ],
  },
  searching: {
    title: "Finding your matches\u2026",
    steps: [
      { icon: "🔎", text: "Searching 2,000+ Cape Town rentals" },
      { icon: "⚖️", text: "Scoring listings against your lifestyle" },
      { icon: "✍️", text: "Building match breakdowns" },
    ],
  },
};

interface Props {
  status: "pending" | "interpreting" | "searching" | "complete" | "failed";
}

export default function ProgressIndicator({ status }: Props) {
  const [activeStep, setActiveStep] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const phase = status === "interpreting" || status === "pending"
    ? PHASES.interpreting
    : status === "searching"
      ? PHASES.searching
      : null;

  useEffect(() => {
    if (!phase) return;
    setActiveStep(0);

    function advance(step: number) {
      setActiveStep(step);
      if (step < phase!.steps.length - 1) {
        timerRef.current = setTimeout(() => advance(step + 1), 2600);
      }
    }

    timerRef.current = setTimeout(() => advance(0), 100);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [status]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!phase) return null;

  return (
    <div className="phase on">
      <div className="ph-hdr">
        <span className="pdot" />
        <span>{phase.title}</span>
      </div>
      <div className="psteps">
        {phase.steps.map((step, i) => (
          <div
            key={i}
            className={`pstep${i === activeStep ? " active" : ""}${i < activeStep ? " done" : ""}`}
          >
            <span className="si">{step.icon}</span>
            {step.text}
          </div>
        ))}
      </div>
    </div>
  );
}
