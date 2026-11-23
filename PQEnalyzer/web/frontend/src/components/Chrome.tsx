import { ChartColumn, ChartLine } from "lucide-react";
import type { ReactNode } from "react";
import { MODE_LABEL, MODES, type Mode } from "../mode";

export function ModeSeg({ mode, onSelect }: { mode: Mode; onSelect: (next: Mode) => void }) {
  return (
    <div className="seg" role="tablist" aria-label="Chart type">
      {MODES.map((key) => (
        <button
          key={key}
          type="button"
          role="tab"
          aria-label={MODE_LABEL[key]}
          aria-selected={mode === key}
          tabIndex={mode === key ? 0 : -1}
          onKeyDown={(event) => {
            const tabs = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
            if (!tabs?.length) return;
            const index = MODES.indexOf(key);
            const next = event.key === "Home" ? 0
              : event.key === "End" ? MODES.length - 1
              : event.key === "ArrowLeft" ? (index + MODES.length - 1) % MODES.length
              : event.key === "ArrowRight" ? (index + 1) % MODES.length
              : null;
            if (next === null) return;
            event.preventDefault();
            onSelect(MODES[next]);
            tabs[next]?.focus();
          }}
          className={mode === key ? "selected" : ""}
          onClick={() => onSelect(key)}
        >
          <span className="seg-label">{MODE_LABEL[key]}</span>
          <span className="seg-icon" aria-hidden="true">
            {key === "series" ? <ChartLine size={16} /> : <ChartColumn size={16} />}
          </span>
        </button>
      ))}
    </div>
  );
}

export function TitleRow({
  title,
  actions,
  onBack,
  className,
}: {
  title: ReactNode;
  actions: ReactNode;
  onBack: () => void;
  className?: string;
}) {
  return (
    <div className={`title-row${className ? ` ${className}` : ""}`}>
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
