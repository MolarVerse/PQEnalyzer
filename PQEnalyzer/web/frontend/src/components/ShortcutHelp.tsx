import { OVERLAY_DEFS } from "./RailBlocks";

/** Every keyboard shortcut the shell offers, in one discoverable place. */
export function ShortcutHelp() {
  return (
    <div className="shortcut-list">
      <div className="shortcut-row">
        <span>
          <kbd>Ctrl</kbd> <kbd>K</kbd>
        </span>
        <span>Search parameters and modes</span>
      </div>
      <div className="shortcut-row">
        <span>
          <kbd>1</kbd> <kbd>2</kbd>
        </span>
        <span>Series / histogram mode</span>
      </div>
      {OVERLAY_DEFS.map((def) => (
        <div className="shortcut-row" key={def.key}>
          <span>
            <kbd>{def.shortcut}</kbd>
          </span>
          <span>
            {def.label} overlay{def.key === "difference" ? " (2 files only)" : ""}
          </span>
        </div>
      ))}
      <div className="shortcut-row">
        <span>
          <kbd>o</kbd>
        </span>
        <span>Overlay / histogram options panel</span>
      </div>
      <div className="shortcut-row">
        <span>
          <kbd>?</kbd>
        </span>
        <span>This help</span>
      </div>
      <div className="shortcut-row">
        <span>
          <kbd>Esc</kbd>
        </span>
        <span>Close panel or dialog, then back to the dashboard</span>
      </div>
    </div>
  );
}
