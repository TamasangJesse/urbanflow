// UrbanFlow — Button.jsx
// Shared component. Used across all features.
// Props: variant, size, loading, disabled, onClick, children, type

import LoadingSpinner from './LoadingSpinner';

const variantClasses = {
  primary:    'bg-[#2C2C2A] text-white hover:bg-[#1a1a18] border border-transparent',
  outline:    'bg-white text-[#2C2C2A] border border-[#2C2C2A] hover:bg-[#F5F5F3]',
  danger:     'bg-[#D85A30] text-white hover:bg-[#c04e27] border border-transparent',
  white:      'bg-white text-[#2C2C2A] hover:bg-[#F5F5F3] border border-white',
  'ghost-blue': 'bg-[#E6F1FB] text-[#185FA5] hover:bg-[#d0e5f7] border border-transparent',
  'ghost-red':  'bg-[#FCEBEB] text-[#A32D2D] hover:bg-[#f8d8d8] border border-transparent',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-[11px]',
  md: 'px-4 py-2 text-[13px]',
  lg: 'px-5 py-2.5 text-[13px]',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  onClick,
  children,
  type = 'button',
  className = '',
}) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-md font-medium transition-colors duration-150
        ${variantClasses[variant] || variantClasses.primary}
        ${sizeClasses[size] || sizeClasses.md}
        ${isDisabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >
      {loading && <LoadingSpinner size="sm" />}
      {children}
    </button>
  );
}
