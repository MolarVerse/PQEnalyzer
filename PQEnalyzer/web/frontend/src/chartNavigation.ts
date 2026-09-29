/** Move among values that actually exist on the visible chart. */
export function inspectIndex(
  indices: number[],
  current: number | null,
  key: string,
): number | null {
  if (indices.length === 0) return null;
  if (key === "Home") return indices[0];
  if (key === "End") return indices[indices.length - 1];
  if (key !== "ArrowLeft" && key !== "ArrowRight") return current;
  if (current === null) {
    return key === "ArrowRight" ? indices[0] : indices[indices.length - 1];
  }
  if (key === "ArrowRight") {
    return indices.find((index) => index > current) ?? indices[indices.length - 1];
  }
  return [...indices].reverse().find((index) => index < current) ?? indices[0];
}
