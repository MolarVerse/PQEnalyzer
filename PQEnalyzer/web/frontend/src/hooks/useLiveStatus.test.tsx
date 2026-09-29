import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useLiveStatus, type ConnectionState } from "./useLiveStatus";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

type Listener = (event: { type: string }) => void;

class StubEventSource {
  static instances: StubEventSource[] = [];
  listeners = new Map<string, Listener[]>();
  closed = false;
  constructor(public url: string) {
    StubEventSource.instances.push(this);
  }
  addEventListener(type: string, listener: Listener) {
    const current = this.listeners.get(type) ?? [];
    current.push(listener);
    this.listeners.set(type, current);
  }
  removeEventListener() {}
  close() {
    this.closed = true;
  }
  emit(type: string) {
    for (const listener of this.listeners.get(type) ?? []) listener({ type });
  }
}

function Probe(callbacks: { onStale: () => void; onReconnect: () => void }) {
  const connection: ConnectionState = useLiveStatus(callbacks);
  return <span data-testid="connection">{connection}</span>;
}

let container: HTMLDivElement;
let root: Root | null = null;

function renderProbe(callbacks: { onStale: () => void; onReconnect: () => void }) {
  act(() => {
    root?.render(<Probe {...callbacks} />);
  });
  return container.querySelector('[data-testid="connection"]')?.textContent;
}

beforeEach(() => {
  StubEventSource.instances = [];
  vi.stubGlobal("EventSource", StubEventSource);
  container = document.createElement("div");
  document.body.appendChild(container);
  act(() => {
    root = createRoot(container);
  });
});

afterEach(() => {
  act(() => {
    root?.unmount();
  });
  root = null;
  container.remove();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("useLiveStatus", () => {
  it("opens an event stream and surfaces stale pushes", () => {
    const onStale = vi.fn();
    const onReconnect = vi.fn();
    expect(renderProbe({ onStale, onReconnect })).toBe("live");
    const source = StubEventSource.instances[0];
    expect(source.url).toBe("/api/events");

    act(() => {
      source.emit("stale");
    });
    expect(onStale).toHaveBeenCalledTimes(1);
  });

  it("flags offline on stream errors and recovers on open", () => {
    const onStale = vi.fn();
    const onReconnect = vi.fn();
    renderProbe({ onStale, onReconnect });
    const source = StubEventSource.instances[0];

    act(() => {
      source.emit("error");
    });
    expect(container.querySelector('[data-testid="connection"]')?.textContent).toBe(
      "offline",
    );
    act(() => {
      source.emit("open");
    });
    expect(container.querySelector('[data-testid="connection"]')?.textContent).toBe(
      "live",
    );
    expect(onReconnect).toHaveBeenCalled();
  });

  it("closes the stream on unmount", () => {
    renderProbe({ onStale: vi.fn(), onReconnect: vi.fn() });
    const source = StubEventSource.instances[0];
    act(() => {
      root?.unmount();
    });
    root = null;
    expect(source.closed).toBe(true);
  });

  it("polls status where EventSource is unavailable", async () => {
    vi.stubGlobal("EventSource", undefined);
    vi.useFakeTimers();
    const onStale = vi.fn();
    const status = { files: [], stale: true };
    const fetch = vi.fn(async () => ({
      ok: true,
      json: async () => status,
    }));
    vi.stubGlobal("fetch", fetch);

    expect(renderProbe({ onStale, onReconnect: vi.fn() })).toBe("polling");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(fetch).toHaveBeenCalledWith("/api/status", expect.anything());
    expect(onStale).toHaveBeenCalledTimes(1);
  });
});
