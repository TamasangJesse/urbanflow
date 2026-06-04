// UrbanFlow — Badge.jsx
// Small red notification badge. Hidden when count is 0.
// Props: count (number), visible (boolean)

export default function Badge({ count = 0, visible = true }) {
  if (!visible || count === 0) return null;

  return (
    <span className="
      inline-flex items-center justify-center
      min-w-[16px] h-4 px-1
      bg-[#D85A30] text-white
      text-[10px] font-medium
      rounded-full leading-none
    ">
      {count > 99 ? '99+' : count}
    </span>
  );
}
