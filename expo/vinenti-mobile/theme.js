import Svg, { Path, Circle } from "react-native-svg";

export const API_BASE_URL = "http://192.168.2.211:5000";

export const COLORS = {
  ink: "#14181D",
  card: "#1B2129",
  parchment: "#ECE7DE",
  muted: "#8B93A0",
  ember: "#C97B4A",
  moss: "#7A8B72",
  rust: "#8B5E3C",
  hairline: "#2A2F36",
};

// Signature mark — a single continuous curved line motif used throughout
// the app (wordmark, icons, loading state).
export function TrunkMark({ size = 22, color = COLORS.ember }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Path
        d="M4 6 C4 10, 10 6, 12 10 C14 14, 8 15, 9 18"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        fill="none"
      />
      <Circle cx="9" cy="18.5" r="1.4" fill={color} />
    </Svg>
  );
}

export function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 21) return "Good evening";
  return "Good night";
}
