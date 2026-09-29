import { useEffect, useState } from "react";

/** Measure the space owned by a chart; ResizeObserver covers viewport changes. */
export function useChartSize(defaultHeight: number) {
  const [element, setElement] = useState<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ w: 760, h: defaultHeight });

  useEffect(() => {
    if (!element) return;
    const measure = () => {
      const w = Math.max(280, Math.round(element.clientWidth));
      const h = Math.max(160, Math.round(element.clientHeight));
      setSize((current) => current.w === w && current.h === h ? current : { w, h });
    };
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    measure();
    return () => observer.disconnect();
  }, [element]);

  return { setElement, size };
}
