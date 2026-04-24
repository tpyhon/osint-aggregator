const colorMap: Record<string, string> = {
  critical: "bg-red-600 text-white",
  high:     "bg-orange-500 text-white",
  medium:   "bg-yellow-400 text-black",
  low:      "bg-blue-400 text-white",
  info:     "bg-gray-400 text-white",
};

export default function SeverityBadge({ severity }: { severity: string | null }) {
  if (!severity) return null;
  const color = colorMap[severity] ?? "bg-gray-300 text-black";
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded ${color}`}>
      {severity.toUpperCase()}
    </span>
  );
}
