import { useCallback, useRef, useState } from "react";
import { autocomplete } from "../api/locations";
import type { AutocompletePrediction, LocationInput } from "../types";

interface ChipDef {
  label: string;
  text: string;
  className: string;
}

interface ChipGroup {
  label: string;
  type: "multi" | "single" | "location";
  chips: ChipDef[];
}

const CHIP_GROUPS: ChipGroup[] = [
  {
    label: "Furnished?",
    type: "multi",
    chips: [
      { label: "🛋 Furnished", text: "fully furnished", className: "cn" },
      { label: "🪑 Semi furnished", text: "semi furnished", className: "cn" },
      { label: "📦 Unfurnished", text: "unfurnished — I have my own furniture", className: "cn" },
    ],
  },
  {
    label: "Bedrooms",
    type: "multi",
    chips: [
      { label: "Studio", text: "a studio or bachelor flat", className: "cn" },
      { label: "1 bed", text: "1 bedroom", className: "cn" },
      { label: "2 beds", text: "2 bedrooms", className: "cn" },
      { label: "3 beds", text: "3 bedrooms", className: "cn" },
      { label: "4+ beds", text: "4 or more bedrooms", className: "cn" },
      { label: "+ Guest bath", text: "with a separate guest bathroom", className: "cn" },
      { label: "En-suite", text: "with en-suite bathrooms", className: "cn" },
    ],
  },
  {
    label: "Monthly budget",
    type: "single",
    chips: [
      { label: "Under R10k", text: "budget under R10,000/month", className: "co" },
      { label: "R10–20k", text: "budget between R10,000 and R20,000/month", className: "co" },
      { label: "R20–35k", text: "budget between R20,000 and R35,000/month", className: "co" },
      { label: "R35–60k", text: "budget between R35,000 and R60,000/month", className: "co" },
      { label: "R60k+", text: "budget above R60,000/month", className: "co" },
    ],
  },
  {
    label: "Area",
    type: "location",
    chips: [
      { label: "Sea Point", text: "in Sea Point", className: "cp" },
      { label: "Green Point", text: "in Green Point", className: "cp" },
      { label: "Camps Bay", text: "in Camps Bay", className: "cp" },
      { label: "Bantry Bay", text: "in Bantry Bay", className: "cp" },
      { label: "Clifton", text: "in Clifton", className: "cp" },
      { label: "Mouille Point", text: "in Mouille Point", className: "cp" },
      { label: "De Waterkant", text: "in De Waterkant", className: "cp" },
      { label: "City Bowl", text: "in City Bowl", className: "cp" },
      { label: "Oranjezicht", text: "in Oranjezicht", className: "cp" },
      { label: "Fresnaye", text: "in Fresnaye", className: "cp" },
      { label: "Woodstock", text: "in Woodstock", className: "cp" },
      { label: "Observatory", text: "in Observatory", className: "cp" },
      { label: "Constantia", text: "in Constantia", className: "cp" },
      { label: "Claremont", text: "in Claremont", className: "cp" },
      { label: "Hout Bay", text: "in Hout Bay", className: "cp" },
      { label: "Bloubergstrand", text: "in Bloubergstrand", className: "cp" },
    ],
  },
  {
    label: "Views & feel",
    type: "multi",
    chips: [
      { label: "🌊 Sea views", text: "with sea views", className: "cg" },
      { label: "⛰ Mountain views", text: "with mountain views", className: "cg" },
      { label: "☀️ Natural sunlight", text: "with lots of natural light and sunlight throughout the day", className: "cg" },
      { label: "🤫 Quiet street", text: "on a quiet street — not on a main or busy road", className: "cg" },
      { label: "🪴 Balcony", text: "with a private balcony or patio", className: "cg" },
      { label: "🏖 Walk to beach", text: "within walking distance of the beach or promenade", className: "cg" },
      { label: "☕ Walkable", text: "in a walkable area with cafés and restaurants nearby", className: "cg" },
      { label: "🌿 Garden", text: "with a garden or private outdoor space", className: "cg" },
      { label: "🌅 Morning sun", text: "east or north-facing for morning sun", className: "cg" },
      { label: "🎨 Trendy area", text: "in a trendy, vibrant neighbourhood", className: "cg" },
    ],
  },
  {
    label: "Building",
    type: "multi",
    chips: [
      { label: "🏊 Pool", text: "with a swimming pool", className: "cb" },
      { label: "💪 Gym", text: "with a gym in the building", className: "cb" },
      { label: "🔒 24hr security", text: "with 24-hour security", className: "cb" },
      { label: "🚗 Parking", text: "with secure parking", className: "cb" },
      { label: "🏠 Double garage", text: "with a double garage", className: "cb" },
      { label: "🛗 Lift", text: "with a lift in the building", className: "cb" },
      { label: "🌐 Fibre", text: "with fibre internet already installed", className: "cb" },
      { label: "⚡ Solar/backup", text: "with solar panels or backup power for load-shedding", className: "cb" },
      { label: "🏡 Boutique", text: "in a small boutique building — not a large complex", className: "cb" },
      { label: "🎩 Concierge", text: "with concierge or building management service", className: "cb" },
    ],
  },
  {
    label: "Lifestyle",
    type: "multi",
    chips: [
      { label: "✨ Modern finishes", text: "in a modern apartment with contemporary finishes and a modern kitchen", className: "cg" },
      { label: "🏗 Open plan", text: "with an open plan kitchen and living area", className: "cg" },
      { label: "🗄 Lots of storage", text: "with lots of built-in cupboards and storage space", className: "cg" },
      { label: "🐾 Pet friendly", text: "where pets are allowed", className: "cg" },
      { label: "💻 Work from home", text: "good for working from home — quiet with fast internet", className: "cg" },
      { label: "✈️ Lock-up-and-go", text: "ideal for a lock-up-and-go lifestyle — I travel frequently", className: "cg" },
      { label: "🥂 For entertaining", text: "great for entertaining — good flow and layout", className: "cg" },
      { label: "👨‍👩‍👧 Family home", text: "suitable for a family with children — safe and spacious", className: "cg" },
      { label: "🎓 Near schools", text: "near good schools", className: "cg" },
      { label: "🚪 Private feel", text: "with a feeling of privacy — not overlooked by neighbours", className: "cg" },
      { label: "📋 Short lease", text: "available on a short lease or month-to-month basis", className: "cg" },
      { label: "💧 Bills included", text: "with water and levies included in the rent", className: "cg" },
    ],
  },
];

const DEMO_PLACES: Record<string, { lat: number; lng: number; sec: string }> = {
  "Sea Point": { lat: -33.9194, lng: 18.3877, sec: "Cape Town, Western Cape" },
  "Camps Bay": { lat: -33.9506, lng: 18.3773, sec: "Cape Town, Western Cape" },
  "Green Point": { lat: -33.9056, lng: 18.4088, sec: "Cape Town, Western Cape" },
  "Clifton": { lat: -33.9375, lng: 18.3741, sec: "Cape Town, Western Cape" },
  "De Waterkant": { lat: -33.9192, lng: 18.4163, sec: "Cape Town, Western Cape" },
  "Mouille Point": { lat: -33.9014, lng: 18.4031, sec: "Cape Town, Western Cape" },
  "Oranjezicht": { lat: -33.9334, lng: 18.4168, sec: "Cape Town, Western Cape" },
  "Fresnaye": { lat: -33.9211, lng: 18.3873, sec: "Cape Town, Western Cape" },
  "Bantry Bay": { lat: -33.9274, lng: 18.3760, sec: "Cape Town, Western Cape" },
  "Hout Bay": { lat: -34.0393, lng: 18.3567, sec: "Cape Town, Western Cape" },
  "Constantia": { lat: -34.0235, lng: 18.4285, sec: "Cape Town, Western Cape" },
  "Woodstock": { lat: -33.9327, lng: 18.4420, sec: "Cape Town, Western Cape" },
  "Observatory": { lat: -33.9408, lng: 18.4693, sec: "Cape Town, Western Cape" },
  "Claremont": { lat: -33.9862, lng: 18.4653, sec: "Cape Town, Western Cape" },
  "Bloubergstrand": { lat: -33.8116, lng: 18.4674, sec: "Cape Town, Western Cape" },
  "City Bowl": { lat: -33.9258, lng: 18.4232, sec: "Cape Town, Western Cape" },
};

interface Props {
  activeChips: Set<string>;
  onToggle: (text: string, isOn: boolean) => void;
  onLocationSelect: (name: string, loc: LocationInput) => void;
  onLocationDeselect: (name: string) => void;
  selectedLocation: LocationInput | null;
  onLocationChange: (loc: LocationInput | null) => void;
}

export default function PreferenceChips({
  activeChips,
  onToggle,
  onLocationSelect,
  onLocationDeselect,
  selectedLocation,
  onLocationChange,
}: Props) {
  const [activeGroup, setActiveGroup] = useState<Record<string, string>>({});
  const [locInput, setLocInput] = useState("");
  const [predictions, setPredictions] = useState<AutocompletePrediction[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleLocInput = useCallback((val: string) => {
    setLocInput(val);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (val.length < 2) {
      setPredictions([]);
      setShowDropdown(false);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      try {
        const preds = await autocomplete(val);
        setPredictions(preds);
        setShowDropdown(preds.length > 0);
      } catch {
        setPredictions([]);
      }
    }, 300);
  }, []);

  const handleSelectPrediction = useCallback(
    (pred: AutocompletePrediction) => {
      onLocationChange({
        name: pred.main_text,
        address: pred.description,
        place_id: pred.place_id,
      });
      setLocInput("");
      setShowDropdown(false);
    },
    [onLocationChange],
  );

  const handleClick = useCallback(
    (group: ChipGroup, chip: ChipDef) => {
      if (group.type === "single") {
        // Deselect current selection in this group
        const currentText = activeGroup[group.label];
        if (currentText && currentText !== chip.text) {
          onToggle(currentText, false);
        }
        if (currentText === chip.text) {
          // Toggle off
          onToggle(chip.text, false);
          setActiveGroup((prev) => {
            const next = { ...prev };
            delete next[group.label];
            return next;
          });
        } else {
          onToggle(chip.text, true);
          setActiveGroup((prev) => ({ ...prev, [group.label]: chip.text }));
        }
      } else if (group.type === "location") {
        const areaName = chip.label;
        const currentArea = activeGroup["Area"];
        if (currentArea && currentArea !== areaName) {
          onLocationDeselect(currentArea);
        }
        if (currentArea === areaName) {
          onLocationDeselect(areaName);
          setActiveGroup((prev) => {
            const next = { ...prev };
            delete next["Area"];
            return next;
          });
        } else {
          const place = DEMO_PLACES[areaName];
          if (place) {
            onLocationSelect(areaName, {
              name: areaName,
              address: `${areaName}, ${place.sec}`,
              lat: place.lat,
              lng: place.lng,
            });
          }
          setActiveGroup((prev) => ({ ...prev, Area: areaName }));
        }
      } else {
        // Multi-select toggle
        const isOn = activeChips.has(chip.text);
        onToggle(chip.text, !isOn);
      }
    },
    [activeChips, activeGroup, onToggle, onLocationSelect, onLocationDeselect],
  );

  const isActive = (group: ChipGroup, chip: ChipDef) => {
    if (group.type === "single") return activeGroup[group.label] === chip.text;
    if (group.type === "location") return activeGroup["Area"] === chip.label;
    return activeChips.has(chip.text);
  };

  return (
    <div className="chips-wrap">
      {CHIP_GROUPS.map((group) => (
        <div className="chip-group" key={group.label}>
          <div className="cg-label">{group.label}</div>

          {group.type === "location" && (
            <div className="places-wrap" style={{ padding: 0, marginBottom: 10, position: "relative" }}>
              {selectedLocation ? (
                <div className="loc-pill" onClick={() => onLocationChange(null)}>
                  📍 {selectedLocation.name}
                  <span className="lp-x">✕</span>
                </div>
              ) : (
                <div className="places-input-row">
                  <input
                    className="places-input"
                    placeholder="Search a suburb or area…"
                    value={locInput}
                    onChange={(e) => handleLocInput(e.target.value)}
                  />
                </div>
              )}

              {showDropdown && (
                <div className="pac-dropdown" style={{ display: "block" }}>
                  {predictions.map((p) => (
                    <div
                      key={p.place_id}
                      className="pac-item"
                      onClick={() => handleSelectPrediction(p)}
                    >
                      <div className="pac-icon">📍</div>
                      <div>
                        <div className="pac-main">{p.main_text}</div>
                        <div className="pac-sub">{p.secondary_text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="cg-row">
            {group.chips.map((chip) => {
              const on = isActive(group, chip);

              return (
                <span
                  key={chip.text}
                  className={`chip ${chip.className}${on ? " on" : ""}`}
                  onClick={() => handleClick(group, chip)}
                >
                  {chip.label}
                  {on && <span className="cx"> ✕</span>}
                </span>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
