import { useEffect, useRef, useState } from "react";

const SIZE = 60;
const POS_KEY = "rythu_wa_pos";

// Floating WhatsApp button: tap opens the chat in WhatsApp style; drag it anywhere on the screen.
// It starts at the bottom-right corner and remembers where it was dropped.
export default function WhatsAppButton({ onOpen, label }) {
  const [pos, setPos] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(POS_KEY));
      if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) return saved;
    } catch { /* storage blocked */ }
    return null; // default corner
  });
  const drag = useRef(null);

  // Keep it on screen when the window gets smaller
  useEffect(() => {
    const fit = () => setPos((p) => p && clamp(p));
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  function down(e) {
    const r = e.currentTarget.getBoundingClientRect();
    drag.current = { dx: e.clientX - r.left, dy: e.clientY - r.top, x0: e.clientX, y0: e.clientY, moved: false };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function move(e) {
    const d = drag.current;
    if (!d) return;
    if (Math.abs(e.clientX - d.x0) + Math.abs(e.clientY - d.y0) > 6) d.moved = true;
    if (d.moved) setPos(clamp({ x: e.clientX - d.dx, y: e.clientY - d.dy }));
  }
  function up() {
    const d = drag.current;
    drag.current = null;
    if (!d) return;
    if (!d.moved) return onOpen();
    setPos((p) => {
      try { localStorage.setItem(POS_KEY, JSON.stringify(p)); } catch { /* storage blocked */ }
      return p;
    });
  }

  const style = pos ? { left: pos.x, top: pos.y } : { right: 20, bottom: 20 };
  return (
    <button className="wa-float" style={style} onPointerDown={down} onPointerMove={move} onPointerUp={up}
            title={label} aria-label={label}>
      <svg viewBox="0 0 32 32" width="34" height="34" aria-hidden="true">
        <path fill="#fff" d="M16 3C8.8 3 3 8.7 3 15.8c0 2.3.6 4.5 1.8 6.5L3 29l6.9-1.8c1.9 1 4 1.6 6.1 1.6 7.2 0 13-5.7 13-12.9C29 8.7 23.2 3 16 3zm0 23.6c-1.9 0-3.8-.5-5.4-1.5l-.4-.2-4.1 1.1 1.1-4-.3-.4c-1.1-1.7-1.7-3.7-1.7-5.7C5.2 9.9 10 5.2 16 5.2S26.8 9.9 26.8 15.8 22 26.6 16 26.6zm5.9-8c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.4-.5-2.6-1.6-1-.9-1.6-1.9-1.8-2.3-.2-.3 0-.5.1-.7l.5-.6c.2-.2.2-.3.3-.6.1-.2 0-.4 0-.6l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.2 1.4 3.4c.2.2 2.4 3.6 5.8 5 .8.4 1.5.6 2 .7.8.3 1.6.2 2.2.1.7-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/>
      </svg>
    </button>
  );
}

function clamp(p) {
  return {
    x: Math.min(Math.max(8, p.x), window.innerWidth - SIZE - 8),
    y: Math.min(Math.max(8, p.y), window.innerHeight - SIZE - 8),
  };
}
