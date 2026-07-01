import { useEffect, useRef, useState } from "react";

const PHRASES = [
  " a quiet 2-bedroom near the beach\u2026",
  " something modern with sea views\u2026",
  " a furnished flat, walkable to caf\u00e9s\u2026",
  " a family home with a garden\u2026",
  " a lock-up-and-go with a pool\u2026",
];

export function useTypewriter(active: boolean) {
  const [text, setText] = useState("");
  const idxRef = useRef(0);
  const charRef = useRef(0);
  const deletingRef = useRef(false);
  const pauseRef = useRef(0);

  useEffect(() => {
    if (!active) return;
    let timer: ReturnType<typeof setTimeout>;

    function tick() {
      if (pauseRef.current > 0) {
        pauseRef.current--;
        timer = setTimeout(tick, 60);
        return;
      }
      const phrase = PHRASES[idxRef.current];
      if (!deletingRef.current) {
        charRef.current++;
        setText(phrase.slice(0, charRef.current));
        if (charRef.current === phrase.length) {
          deletingRef.current = true;
          pauseRef.current = 28;
        }
        timer = setTimeout(tick, 68);
      } else {
        charRef.current--;
        setText(phrase.slice(0, charRef.current));
        if (charRef.current === 0) {
          deletingRef.current = false;
          idxRef.current = (idxRef.current + 1) % PHRASES.length;
          pauseRef.current = 5;
        }
        timer = setTimeout(tick, 32);
      }
    }

    timer = setTimeout(tick, 800);
    return () => clearTimeout(timer);
  }, [active]);

  return text;
}
