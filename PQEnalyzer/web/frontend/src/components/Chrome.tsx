import type { ReactNode } from "react";
import { MODE_LABEL, MODES, type Mode } from "../mode";

export function ModeSeg({ mode, onSelect }: { mode: Mode; onSelect: (next: Mode) => void }) {
  return (
    <div className="seg" role="tablist" aria-label="Display mode">
      {MODES.map((key) => (
        <button
          key={key}
          type="button"
          role="tab"
          aria-selected={mode === key}
          className={mode === key ? "selected" : ""}
          onClick={() => onSelect(key)}
        >
          {MODE_LABEL[key]}
        </button>
      ))}
    </div>
  );
}

export function TitleRow({
  title,
  actions,
  onBack,
}: {
  title: ReactNode;
  actions: ReactNode;
  onBack: () => void;
}) {
  return (
    <div className="title-row">
      <button
        type="button"
        className="ghost-action"
        onClick={onBack}
        title="Back to all parameters"
      >
        <span aria-hidden="true">←</span>
        All
      </button>
      <h2 className="section-title">{title}</h2>
      <div className="title-actions">{actions}</div>
    </div>
  );
}
