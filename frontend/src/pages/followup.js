// Remedy follow-up asked from the 🔔 bell: "did you use it, when, did it work?"
// Each step has a question and quick-reply buttons; the answers are saved to History.

const REASONS = [
  ["Could not afford it", "కొనలేకపోయాను"],
  ["Not available in the shop", "దుకాణంలో దొరకలేదు"],
  ["Used something else", "వేరే మందు వాడాను"],
  ["Problem went away on its own", "దానంతట అదే తగ్గింది"],
  ["Waiting to confirm with AEO", "AEO తో నిర్ధారించాలి"],
  ["Other", "ఇతర కారణం"],
];

function ago(iso, te) {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return te ? "ఈరోజు" : "Today";
  if (days === 1) return te ? "నిన్న" : "Yesterday";
  return te ? `${days} రోజుల క్రితం` : `${days} days ago`;
}

function daysBack(n, rec) {
  const d = new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
  const spotted = rec.created_on.slice(0, 10);
  return d < spotted ? spotted : d;
}

// cropName / med: optional functions giving the Telugu crop and medicine names
export function intro(rec, te, cropName = (c) => c, med = (m) => m) {
  const product = med(rec.remedies[0]?.product);
  return te
    ? `📝 **మందు పనిచేసిందా?**\n${ago(rec.created_on, te)} మీ ${cropName(rec.crop)} పంటలో **${rec.disease_te}** కనిపించింది. మేము **${product}** వాడమని సూచించాము.`
    : `📝 **Quick check on your crop**\n${ago(rec.created_on, te)} we found **${rec.disease}** on your ${rec.crop} and suggested **${product}**.`;
}

// Returns {question, options: [{value, label}]} for a step
export function step(name, rec, te, med = (m) => m) {
  switch (name) {
    case "used":
      return { question: te ? "మీరు ఆ మందు వాడారా?" : "Did you use the remedy?", options: [
        { value: "yes", label: te ? "✅ వాడాను" : "✅ Used it" },
        { value: "partly", label: te ? "🌓 కొంత వాడాను" : "🌓 Used partly" },
        { value: "no", label: te ? "❌ వాడలేదు" : "❌ Did not use" },
      ] };
    case "product":
      return { question: te ? "ఏ మందు వాడారు?" : "Which one did you use?", options: [
        ...rec.remedies.map((m) => ({ value: m.product, label: `${m.kind === "Organic" ? "🌿" : "🧪"} ${med(m.product)}` })),
        { value: "Something else", label: te ? "వేరే మందు" : "Something else" },
      ] };
    case "when": {
      // Only offer times after the disease was spotted (no "Last week" for a 3-day-old case)
      const since = Math.floor((Date.now() - new Date(rec.created_on).getTime()) / 86400000);
      const times = [[0, "Today", "ఈరోజు"], [1, "Yesterday", "నిన్న"], [3, "This week", "ఈ వారం"],
                     [8, "Last week", "గత వారం"], [16, "Earlier", "అంతకు ముందు"]].filter(([n]) => n <= since);
      return { question: te ? "ఎప్పుడు పిచికారీ చేశారు?" : "When did you spray?",
        options: times.map(([n, en, t]) => ({ value: daysBack(n, rec), label: te ? t : en })) };
    }
    case "result":
      return { question: te ? "ఫలితం ఎలా ఉంది?" : "How did it work?", options: [
        { value: "cured", label: te ? "✅ పూర్తిగా తగ్గింది" : "✅ Cured" },
        { value: "improved", label: te ? "👍 మెరుగుపడింది" : "👍 Improved" },
        { value: "no_change", label: te ? "➖ మార్పు లేదు" : "➖ No change" },
        { value: "worse", label: te ? "👎 ఎక్కువైంది" : "👎 Got worse" },
      ] };
    default: // reason
      return { question: te ? "ఎందుకు వాడలేదు?" : "Why didn't you use it?",
        options: REASONS.map(([en, t]) => ({ value: en, label: te ? t : en })) };
  }
}

// Which step comes after this answer; null = all done
export function next(name, value, rec) {
  if (name === "used") return value === "no" ? "reason" : rec.remedies.length > 1 ? "product" : "when";
  if (name === "product") return "when";
  if (name === "when") return "result";
  return null;
}

export const FIELD = { used: "used", product: "product", when: "applied_on", result: "result", reason: "reason" };

export const text = {
  thanks: (te) => (te ? "🙏 ధన్యవాదాలు! మీ సమాధానం **📜 నా చరిత్ర** లో సేవ్ అయింది. ఇది ఇతర రైతులకు కూడా సహాయపడుతుంది." : "🙏 Thank you! Your answer is saved in **📜 My history**. It helps other farmers too."),
  sorry: (te) => (te ? "ఫలితం బాగోలేదు. మీ AEO ని సంప్రదించండి లేదా **పంట వైద్యుడు** లో మళ్లీ ఫోటో పంపండి." : "Sorry it did not work. Please contact your AEO, or send a new photo in **Crop Doctor**."),
};
