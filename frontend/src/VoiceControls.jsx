import { useLang } from "./i18n.jsx";
import { pauseSpeaking, resumeSpeaking, stopSpeaking, useVoice } from "./speech.js";

// Small ⏸ / ▶ and ⏹ icons for whatever is being read aloud. They show only once the reading has
// started, beside the Read aloud button (or in the chat's voice bar).
export default function VoiceControls({ onStop }) {
  const { t } = useLang();
  const voice = useVoice();
  if (voice !== "speaking" && voice !== "paused") return null;
  return (
    <>
      <button className="voice-icon" onClick={voice === "paused" ? resumeSpeaking : pauseSpeaking}
              title={voice === "paused" ? t("Continue", "కొనసాగించండి") : t("Pause", "ఆపి ఉంచండి")}>
        {voice === "paused" ? "▶" : "⏸"}</button>
      <button className="voice-icon" onClick={onStop || stopSpeaking} title={t("Stop", "ఆపండి")}>⏹</button>
    </>
  );
}
