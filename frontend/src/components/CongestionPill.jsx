// UrbanFlow — CongestionPill.jsx
// Renders a colored pill for congestion levels: Low / Medium / High / Very High
// Props: level ('Low' | 'Medium' | 'High' | 'Very High')

const levelStyles = {
  'Low':       { bg: '#EAF3DE', text: '#639922' },
  'Medium':    { bg: '#FAEEDA', text: '#BA7517' },
  'High':      { bg: '#FCEBEB', text: '#D85A30' },
  'Very High': { bg: '#FCEBEB', text: '#A32D2D' },
};

export default function CongestionPill({ level = 'Low' }) {
  const style = levelStyles[level] || levelStyles['Low'];

  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {level}
    </span>
  );
}
