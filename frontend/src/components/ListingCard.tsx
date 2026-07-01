import { useCallback, useRef } from "react";
import type { SearchResult } from "../types";

interface Props {
  result: SearchResult;
  index: number;
  isSaved: boolean;
  onToggleSave: (result: SearchResult) => void;
  fallbackImg: (location: string | null) => string;
}

export default function ListingCard({ result, index, isSaved, onToggleSave, fallbackImg }: Props) {
  const btnRef = useRef<HTMLButtonElement>(null);
  const sc = (result.match_score ?? 0) >= 80 ? "mshi" : (result.match_score ?? 0) >= 60 ? "msmi" : "mslo";
  const imgSrc = result.image_url || fallbackImg(result.location);
  const fb = fallbackImg(result.location);
  const amenities = result.amenities || [];

  const handleSave = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onToggleSave(result);
      if (btnRef.current) {
        btnRef.current.style.transform = "scale(1.25)";
        setTimeout(() => {
          if (btnRef.current) btnRef.current.style.transform = "";
        }, 200);
      }
    },
    [result, onToggleSave],
  );

  return (
    <div className="card" style={{ animationDelay: `${index * 70}ms` }}>
      <div
        className="cimg-wrap"
        style={result.url ? { cursor: "pointer" } : undefined}
        onClick={() => result.url && window.open(result.url, "_blank")}
      >
        <img
          src={imgSrc}
          alt=""
          loading="lazy"
          onError={(e) => {
            (e.target as HTMLImageElement).src = fb;
          }}
        />
        <div className="crank-badge">{index + 1}</div>
        <button
          ref={btnRef}
          className={`save-btn${isSaved ? " saved" : ""}`}
          onClick={handleSave}
        >
          {isSaved ? "❤️" : "🤍"}
        </button>
        {result.availability === "rare" ? (
          <div className="avail-badge av-rare">✦ Rare find</div>
        ) : (
          <div className="avail-badge av-now">● Available now</div>
        )}
      </div>

      <div className="cbody">
        <div className="ctop">
          <div className="ctitle">
            {result.url ? (
              <a href={result.url} target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>
                {result.title || "Rental"}
              </a>
            ) : (
              result.title || "Rental"
            )}
          </div>
          <div className="cprice">{result.price || "POA"}</div>
        </div>

        <div className="cloc">📍 {result.location || ""}</div>

        <div className="cstats">
          {result.beds != null && <span className="cstat">🛏 {result.beds} bed{result.beds > 1 ? "s" : ""}</span>}
          {result.baths != null && <span className="cstat">🚿 {result.baths} bath{result.baths > 1 ? "s" : ""}</span>}
          {result.size && <span className="cstat">📐 {result.size}</span>}
        </div>

        <div className="cpills">
          {result.furnished === true && <span className="pill pb">🛋 Furnished</span>}
          {result.furnished === false && <span className="pill pb">📦 Unfurnished</span>}
          {result.lease && <span className="pill pb">📋 {result.lease}</span>}
          {result.pets === true && <span className="pill py">🐾 Pets OK</span>}
          {result.pets === false && <span className="pill pn">🚫 No pets</span>}
          {result.source && <span className="pill ps">via {result.source}</span>}
        </div>

        {amenities.length > 0 && (
          <div className="ctags">
            {amenities.slice(0, 4).map((a, i) => (
              <span key={i} className="ctag">{a}</span>
            ))}
            {amenities.length > 4 && <span className="ctag">+{amenities.length - 4}</span>}
          </div>
        )}

        <div className="match-section">
          <div className="match-top">
            <div className={`mscore ${sc}`}>{result.match_score ?? "?"}%</div>
            <div className="mreason">{result.match_reason || ""}</div>
          </div>

          {((result.matched?.length || 0) > 0 || (result.not_matched?.length || 0) > 0) && (
            <div className="match-lists">
              <div>
                <div className="ml-hdr ml-hdr-yes">✓ Matched</div>
                {(result.matched || []).map((m, i) => (
                  <div key={i} className="ml-item ml-yes">
                    <span className="ml-icon">✓</span>{m}
                  </div>
                ))}
                {!(result.matched?.length) && (
                  <div className="ml-item ml-yes"><span className="ml-icon">✓</span>See listing</div>
                )}
              </div>
              <div>
                <div className="ml-hdr ml-hdr-no">✗ Not confirmed</div>
                {(result.not_matched || []).map((m, i) => (
                  <div key={i} className="ml-item ml-no">
                    <span className="ml-icon">✗</span>{m}
                  </div>
                ))}
                {!(result.not_matched?.length) && (
                  <div style={{ fontSize: "11.5px", color: "var(--ri3)", padding: "4px 0" }}>Nothing flagged</div>
                )}
              </div>
            </div>
          )}

          {result.url && (
            <a className="clink" href={result.url} target="_blank" rel="noopener noreferrer">
              View full listing on {result.source || "Property24"} →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
