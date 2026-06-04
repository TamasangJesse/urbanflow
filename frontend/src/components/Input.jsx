// UrbanFlow — Input.jsx
// Shared form input. Always renders label above, error/hint below.
// Props: label, type, placeholder, value, onChange, error, hint, name, id, disabled, autoComplete

export default function Input({
  label,
  type = 'text',
  placeholder = '',
  value,
  onChange,
  error,
  hint,
  name,
  id,
  disabled = false,
  autoComplete,
  className = '',
}) {
  const inputId = id || name || label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-[11px] font-medium text-[#2C2C2A] uppercase tracking-wide"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        autoComplete={autoComplete}
        className={`
          w-full px-3 py-2 text-[13px] text-[#2C2C2A]
          bg-white border rounded-md outline-none
          placeholder:text-[#5F5E5A] placeholder:opacity-60
          transition-colors duration-150
          ${error
            ? 'border-[#D85A30] focus:border-[#D85A30] focus:ring-1 focus:ring-[#D85A30]'
            : 'border-[#E8E6DF] focus:border-[#378ADD] focus:ring-1 focus:ring-[#378ADD]'
          }
          ${disabled ? 'opacity-60 cursor-not-allowed bg-[#F5F5F3]' : ''}
        `}
      />
      {error && (
        <p className="text-[11px] text-[#D85A30] mt-0.5">{error}</p>
      )}
      {hint && !error && (
        <p className="text-[11px] text-[#5F5E5A] mt-0.5">{hint}</p>
      )}
    </div>
  );
}
