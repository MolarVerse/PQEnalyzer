import uPlot from "uplot";
import type { LineDataset } from "../charts";

interface Endpoint {
  t: number;
  v: number;
  color: string;
}

interface ExportOptions {
  source: HTMLCanvasElement;
  plot: uPlot;
  visible: LineDataset[];
  markers: { value: number; label: string }[];
  endpoints: Endpoint[];
  caption?: string;
}

/** Compose the plot canvas with the annotations shown in the browser. */
export function chartPNG({ source, plot, visible, markers, endpoints, caption }: ExportOptions): string | null {
  const ratio = source.width / plot.width;
  if (!Number.isFinite(ratio) || ratio <= 0) return null;
  const header = 10 + visible.length * 18;
  const footer = caption ? 26 : 0;
  const output = document.createElement("canvas");
  output.width = source.width;
  output.height = source.height + Math.round((header + footer) * ratio);
  const ctx = output.getContext("2d");
  if (!ctx) return null;

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, output.width, output.height);
  ctx.drawImage(source, 0, Math.round(header * ratio));
  ctx.scale(ratio, ratio);
  ctx.font = '11px "IBM Plex Mono", "JetBrains Mono", monospace';
  visible.forEach((dataset, index) => {
    const y = 17 + index * 18;
    ctx.strokeStyle = dataset.color;
    ctx.lineWidth = 2;
    ctx.setLineDash(dataset.dash?.split(" ").map(Number) ?? []);
    ctx.beginPath();
    ctx.moveTo(12, y - 3);
    ctx.lineTo(34, y - 3);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#161616";
    ctx.fillText(dataset.label, 42, y);
  });

  const left = plot.bbox.left / uPlot.pxRatio;
  const top = header + plot.bbox.top / uPlot.pxRatio;
  const height = plot.bbox.height / uPlot.pxRatio;
  const min = plot.scales.x.min;
  const max = plot.scales.x.max;
  markers.forEach((marker, index) => {
    if (min == null || max == null || marker.value < min || marker.value > max) return;
    const x = left + plot.valToPos(marker.value, "x");
    ctx.strokeStyle = "#8d8d8d";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, top + height);
    ctx.stroke();
    ctx.setLineDash([]);
    const labelY = top + 14 + (index % 2) * 14;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(x + 3, labelY - 11, ctx.measureText(marker.label).width + 8, 15);
    ctx.fillStyle = "#393939";
    ctx.fillText(marker.label, x + 7, labelY);
  });
  endpoints.forEach((point) => {
    if (min == null || max == null || point.t < min || point.t > max) return;
    const x = left + plot.valToPos(point.t, "x");
    const y = top + plot.valToPos(point.v, "y");
    ctx.fillStyle = point.color;
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fill();
  });
  if (caption) {
    ctx.fillStyle = "#6f6f6f";
    ctx.fillText(caption, 12, header + plot.height + 17);
  }
  try {
    return output.toDataURL("image/png");
  } catch {
    return null;
  }
}
