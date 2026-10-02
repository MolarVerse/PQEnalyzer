import { describe, expect, it } from "vitest";
import {
  defaultSettings,
  loadSettings,
  saveSettings,
  SETTINGS_KEY,
  type StorageLike,
} from "./settings";

function memoryStorage(seed?: Record<string, string>): StorageLike {
  const map = new Map(Object.entries(seed ?? {}));
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => {
      map.set(key, value);
    },
  };
}

describe("loadSettings", () => {
  it("returns defaults without storage", () => {
    expect(loadSettings(null)).toEqual(defaultSettings());
    expect(loadSettings(undefined)).toEqual(defaultSettings());
  });

  it("returns defaults for missing, corrupt, or versioned-out payloads", () => {
    expect(loadSettings(memoryStorage()).overlays).toEqual({ mean: true });
    expect(loadSettings(memoryStorage({ [SETTINGS_KEY]: "not json" }))).toEqual(
      defaultSettings(),
    );
    expect(
      loadSettings(memoryStorage({ [SETTINGS_KEY]: '{"version":2}' })),
    ).toEqual(defaultSettings());
  });

  it("round-trips valid settings", () => {
    const storage = memoryStorage();
    saveSettings(storage, {
      version: 1,
      overlays: { mean: true, running_average: true },
      sortMode: "drift",
    });
    const loaded = loadSettings(storage);
    expect(loaded.overlays).toEqual({ mean: true, running_average: true });
    expect(loaded.sortMode).toBe("drift");
  });

  it("drops retired run comparisons and unknown overlay keys", () => {
    const loaded = loadSettings(
      memoryStorage({
        [SETTINGS_KEY]: JSON.stringify({
          version: 1,
          overlays: {
            mean: false,
            cummulative_average: true,
            difference: true,
            frobnicate: true,
          },
          sortMode: "name",
        }),
      }),
    );
    expect(loaded.overlays).toEqual({
      mean: false,
      cumulative_average: true,
    });
  });

  it("maps the old self-correlation preference to autocorrelation", () => {
    const loaded = loadSettings(memoryStorage({
      [SETTINGS_KEY]: JSON.stringify({
        version: 1,
        overlays: { mean: false, self_correlation_mean: true },
        sortMode: "name",
      }),
    }));
    expect(loaded.overlays).toEqual({ autocorrelation: true });
  });

  it("keeps defaults for malformed sort and ignores retired bounds", () => {
    const loaded = loadSettings(
      memoryStorage({
        [SETTINGS_KEY]: JSON.stringify({
          version: 1,
          overlays: {},
          softBounds: { min: 5, max: null },
          sortMode: "volcano",
        }),
      }),
    );
    expect(loaded).not.toHaveProperty("softBounds");
    expect(loaded.sortMode).toBe("name");
  });

  it("restores autocorrelation as the sole chart mode", () => {
    const loaded = loadSettings(memoryStorage({
      [SETTINGS_KEY]: JSON.stringify({
        version: 1,
        overlays: { mean: true, running_average: true, autocorrelation: true },
      }),
    }));
    expect(loaded.overlays).toEqual({ autocorrelation: true });
  });
});
