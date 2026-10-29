import { useRef } from "react";
import { useLang } from "./i18n.jsx";

// Photos and videos of a sick crop: add as many as you like, see them as thumbnails, ✕ removes one.
// items: [{ file, url, video }]
export const toItems = (files) =>
  [...files].map((file) => ({ file, url: URL.createObjectURL(file), video: file.type.startsWith("video/") }));

export function mediaForm(items) {
  const form = new FormData();
  items.forEach((m) => form.append("files", m.file));
  return form;
}

export default function MediaPicker({ items, onChange }) {
  const { t } = useLang();
  const input = useRef(null);
  const nPhotos = items.filter((m) => !m.video).length, nVideos = items.length - nPhotos;
  const add = (files) => files?.length && onChange([...items, ...toItems(files)]);
  const remove = (i) => onChange(items.filter((_, j) => j !== i));

  return (
    <div className={`dropzone media-drop ${items.length ? "has" : ""}`}
         onClick={() => !items.length && input.current.click()}
         onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); add(e.dataTransfer.files); }}>
      {items.length ? (
        <div className="media-grid">
          {items.map((m, i) => (
            <div key={m.url} className="media-thumb">
              {m.video ? <video src={m.url} muted playsInline /> : <img src={m.url} alt="" />}
              {m.video && <span className="media-badge">🎬</span>}
              <button className="media-x" title={t("Remove", "తీసివేయండి")} onClick={(e) => { e.stopPropagation(); remove(i); }}>✕</button>
            </div>
          ))}
          <button className="media-add" onClick={(e) => { e.stopPropagation(); input.current.click(); }}>
            ＋<small>{t("Add more", "ఇంకా జోడించండి")}</small>
          </button>
        </div>
      ) : (
        <div>
          <div className="big-icon">📷 🎬</div>
          {t("Choose or take photos / videos", "ఫోటోలు / వీడియోలు ఎంచుకోండి లేదా తీయండి")}<br />
          <small className="muted">{t("Add as many as you like · photos up to 8 MB, videos up to 50 MB",
            "ఎన్నైనా జోడించవచ్చు · ఫోటో 8 MB, వీడియో 50 MB వరకు")}</small>
        </div>
      )}
      {items.length > 0 && (
        <small className="muted media-count">
          {t(`${nPhotos} photo${nPhotos === 1 ? "" : "s"} · ${nVideos} video${nVideos === 1 ? "" : "s"}`,
            `${nPhotos} ${nPhotos === 1 ? "ఫోటో" : "ఫోటోలు"} · ${nVideos} ${nVideos === 1 ? "వీడియో" : "వీడియోలు"}`)}
        </small>
      )}
      <input ref={input} type="file" accept="image/*,video/*" multiple hidden
             onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
    </div>
  );
}
