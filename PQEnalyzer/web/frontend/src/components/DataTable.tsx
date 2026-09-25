import { Fragment } from "react";
import { formatValue } from "../api";
import type { HistogramTableData, SeriesTableData } from "../tables";

function cell(value: number | null) {
  return value === null || !Number.isFinite(value) ? (
    <span className="data-null">—</span>
  ) : (
    formatValue(value)
  );
}

/**
 * Transported series points (the values the chart draws), one row per
 * index with a time+value pair per file. Full resolution via CSV export.
 */
export function SeriesDataTable({ data }: { data: SeriesTableData }) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">#</th>
            {data.files.map((file) => (
              <th scope="col" key={file.label} colSpan={2}>
                {file.label}
              </th>
            ))}
          </tr>
          <tr>
            <th scope="col" />
            {data.files.map((file) => (
              <Fragment key={file.label}>
                <th scope="col">
                  time{data.timeUnit ? ` (${data.timeUnit})` : ""}
                </th>
                <th scope="col">
                  value
                </th>
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.body.map((pairs, index) => (
            <tr key={index}>
              <th scope="row">{index + 1}</th>
              {pairs.map(([time, value], fileIndex) => (
                <Fragment key={fileIndex}>
                  <td>{cell(time)}</td>
                  <td>{cell(value)}</td>
                </Fragment>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Binned counts behind the histogram chart (all bins, never truncated). */
export function HistogramDataTable({ data }: { data: HistogramTableData }) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">bin</th>
            <th scope="col">lower</th>
            <th scope="col">upper</th>
            {data.files.map((file) => (
              <th scope="col" key={file.label}>
                {file.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.bins.map((bin, index) => (
            <tr key={index}>
              <th scope="row">{index + 1}</th>
              <td>{cell(bin.lower)}</td>
              <td>{cell(bin.upper)}</td>
              {bin.counts.map((count, fileIndex) => (
                <td key={fileIndex}>{count.toLocaleString()}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
