// UrbanFlow — LoadingSpinner.jsx
// Used inside Button (loading state) and as full-page loader.

const sizeMap = {
  sm: 'w-3.5 h-3.5 border-[1.5px]',
  md: 'w-5 h-5 border-2',
  lg: 'w-8 h-8 border-2',
};

export default function LoadingSpinner({ size = 'md', color = 'currentColor' }) {
  return (
    <span
      className={`
        inline-block rounded-full border-transparent animate-spin
        ${sizeMap[size] || sizeMap.md}
      `}
      style={{
        borderTopColor: color === 'currentColor' ? 'currentColor' : color,
        borderRightColor: 'transparent',
        borderBottomColor: 'transparent',
        borderLeftColor: 'transparent',
        borderStyle: 'solid',
      }}
      aria-label="Loading"
    />
  );
}

/**
 * Full-page loading state — centers the spinner on screen.
 */
export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F3]">
      <LoadingSpinner size="lg" color="#378ADD" />
    </div>
  );
}
