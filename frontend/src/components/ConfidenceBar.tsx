interface Props {
  value: number; // 0-1
  label?: string;
}

export default function ConfidenceBar({ value, label }: Props) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "#2f9e44" : pct >= 40 ? "#e8890c" : "#c92a2a";

  return (
    <div className="confidence-bar">
      {label && <span className="confidence-label">{label}</span>}
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="confidence-pct">{pct}%</span>
    </div>
  );
}
