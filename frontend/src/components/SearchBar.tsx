import { useCallback, useEffect, useRef, useState } from "react";
import { useTypewriter } from "../hooks/useTypewriter";

interface Props {
  query: string;
  onQueryChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function SearchBar({
  query,
  onQueryChange,
  onSubmit,
}: Props) {
  const taRef = useRef<HTMLTextAreaElement>(null);
  const [twActive, setTwActive] = useState(!query);
  const twText = useTypewriter(twActive);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onSubmit();
      }
    },
    [onSubmit],
  );

  useEffect(() => {
    if (query && twActive) setTwActive(false);
  }, [query, twActive]);

  return (
    <div className="chatbar">
      <div className="tw-label">
        <span className="tw-static">I am looking for </span>
        {twActive && (
          <>
            <span className="tw-typed">{twText}</span>
            <span className="tw-cursor" />
          </>
        )}
      </div>

      <textarea
        ref={taRef}
        className="cta"
        rows={3}
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => twActive && setTwActive(false)}
        placeholder="…a quiet 2-bed with a sea-facing balcony, natural light, walkable to cafés, modern building with a pool…"
      />
    </div>
  );
}
