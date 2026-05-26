// UrbanFlow — LandingPage.jsx
// Public page — no auth required, no API calls, no hooks.
// Pure layout and Tailwind styling only. Golden Rule: NO fetch() here.

import { Link } from 'react-router-dom';

function NavBar() {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between bg-[#F7F6F2]/90 backdrop-blur-lg border-b border-[#E2E1DB]"
      style={{ height: '68px', paddingLeft: '24px', paddingRight: '24px' }}
    >
      <span className="text-[20px] font-bold select-none" style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.4px' }}>
        <span className="text-[#111210]">Urban</span>
        <span className="text-[#2563EB]">Flow</span>
      </span>

      {/* Nav links — hidden on mobile */}
      <div className="hidden md:flex items-center gap-8">
        <a href="#how-it-works" className="text-[14px] font-medium text-[#7A7A72] hover:text-[#111210] transition-colors">How it works</a>
        <a href="#features"     className="text-[14px] font-medium text-[#7A7A72] hover:text-[#111210] transition-colors">Features</a>
      </div>

      <div className="flex items-center gap-2">
        <Link
          to="/login"
          className="px-4 py-2 rounded-lg text-[13px] font-medium text-[#3D3D38] border border-[#C8C7BF] hover:bg-[#EFEDE7] hover:border-[#7A7A72] transition-colors"
        >
          Log in
        </Link>
        <Link
          to="/register"
          className="px-4 py-2 rounded-lg text-[13px] font-semibold text-white bg-[#111210] hover:bg-[#3D3D38] transition-colors"
          style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.25)' }}
        >
          Get started
        </Link>
      </div>
    </nav>
  );
}

function MapIllustration() {
  return (
    <div
      className="bg-white border border-[#E2E1DB] rounded-[20px] overflow-hidden w-full"
      style={{ boxShadow: '0 32px 64px rgba(17,18,16,0.12), 0 12px 30px rgba(17,18,16,0.08)' }}
    >
      {/* Card header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E1DB] bg-white">
        <span className="text-[13px] font-semibold text-[#3D3D38]">Yaoundé — Live Traffic</span>
        <span className="flex items-center gap-1.5 text-[11.5px] font-medium text-green-600 bg-green-50 border border-green-200 rounded-full px-2.5 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          Live
        </span>
      </div>

      {/* Map body */}
      <div className="relative bg-[#EDE9E0]" style={{ height: '280px' }}>
        {/* Floating alert pill */}
        <div
          className="absolute top-9 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-white border border-[#E2E1DB] rounded-full px-4 py-1.5 text-[12.5px] font-medium text-[#3D3D38] whitespace-nowrap z-10"
          style={{ boxShadow: '0 4px 12px rgba(17,18,16,0.08)' }}
        >
          <span>⚠️</span>
          Incident near Carrefour Nlongkak
        </div>

        <svg width="100%" height="100%" viewBox="0 0 480 310" xmlns="http://www.w3.org/2000/svg">
          <rect width="480" height="310" fill="#EDE9E0"/>
          {/* City blocks */}
          <rect x="0"   y="0"   width="100" height="80"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="120" y="0"   width="120" height="80"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="260" y="0"   width="100" height="80"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="380" y="0"   width="100" height="80"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="0"   y="100" width="100" height="90"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="120" y="100" width="120" height="90"  rx="2" fill="#EAC89A" fillOpacity="0.45"/>
          <rect x="260" y="100" width="100" height="90"  rx="2" fill="#F4A574" fillOpacity="0.38"/>
          <rect x="380" y="100" width="100" height="90"  rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="0"   y="210" width="100" height="100" rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="120" y="210" width="120" height="100" rx="2" fill="#EAC89A" fillOpacity="0.38"/>
          <rect x="260" y="210" width="100" height="100" rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          <rect x="380" y="210" width="100" height="100" rx="2" fill="#E0DCD2" fillOpacity="0.7"/>
          {/* Roads */}
          <rect x="100" y="0"   width="20" height="310" fill="white" fillOpacity="0.8"/>
          <rect x="240" y="0"   width="20" height="310" fill="white" fillOpacity="0.8"/>
          <rect x="360" y="0"   width="20" height="310" fill="white" fillOpacity="0.8"/>
          <rect x="0"   y="80"  width="480" height="20" fill="white" fillOpacity="0.8"/>
          <rect x="0"   y="195" width="480" height="20" fill="white" fillOpacity="0.8"/>
          {/* Blue dashed route */}
          <polyline
            points="70,270 110,270 110,195 180,195 180,90 250,90 300,40 420,40"
            fill="none" stroke="#2563EB" strokeWidth="3"
            strokeDasharray="8 5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9"
          />
          {/* Destination pin */}
          <circle cx="420" cy="40" r="10" fill="#2563EB"/>
          <circle cx="420" cy="40" r="5"  fill="white"/>
          {/* Origin pin */}
          <circle cx="70" cy="270" r="10" fill="#2563EB" fillOpacity="0.25"/>
          <circle cx="70" cy="270" r="6"  fill="#2563EB"/>
          <circle cx="70" cy="270" r="3"  fill="white"/>
          {/* Incident pin */}
          <circle cx="180" cy="145" r="14" fill="#EF4444" fillOpacity="0.15"/>
          <circle cx="180" cy="145" r="10" fill="#EF4444"/>
          <text x="180" y="149" textAnchor="middle" fontFamily="sans-serif" fontSize="11" fontWeight="bold" fill="white">!</text>
          {/* Neighbourhood labels */}
          <text x="200" y="74"  fontFamily="sans-serif" fontSize="10" fill="#8A8478" textAnchor="middle">Bastos</text>
          <text x="80"  y="160" fontFamily="sans-serif" fontSize="10" fill="#8A8478" textAnchor="middle">Mvog-Mbi</text>
          <text x="310" y="160" fontFamily="sans-serif" fontSize="10" fill="#8A8478" textAnchor="middle">Melen</text>
          <text x="200" y="255" fontFamily="sans-serif" fontSize="10" fill="#8A8478" textAnchor="middle">Biyem-Assi</text>
        </svg>

        {/* Legend */}
        <div
          className="absolute bottom-3 right-3 bg-white/90 backdrop-blur border border-[#E2E1DB] rounded-xl px-3.5 py-2.5"
          style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.06)' }}
        >
          <div className="text-[10px] font-semibold text-[#7A7A72] uppercase tracking-wide mb-1.5">Congestion</div>
          <div className="flex items-center gap-1.5 text-[12px] text-[#3D3D38] mb-1">
            <span className="w-2 h-2 rounded-sm bg-[#D4D0C8]" />Low
          </div>
          <div className="flex items-center gap-1.5 text-[12px] text-[#3D3D38] mb-1">
            <span className="w-2 h-2 rounded-sm bg-[#EAC89A]" />Medium
          </div>
          <div className="flex items-center gap-1.5 text-[12px] text-[#3D3D38]">
            <span className="w-2 h-2 rounded-sm bg-[#F4A574]" />High
          </div>
        </div>
      </div>
    </div>
  );
}

function HeroSection() {
  return (
    <section
      className="min-h-screen bg-[#F7F6F2] relative overflow-hidden"
      style={{ paddingTop: '88px' }}
    >
      {/* Subtle grid texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          backgroundImage: 'linear-gradient(#E2E1DB 1px, transparent 1px), linear-gradient(90deg, #E2E1DB 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      {/* Radial vignette over grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 65% 60% at 50% 50%, transparent 40%, #F7F6F2 100%)' }}
      />

      {/* Two-column on desktop, single column on mobile */}
      <div
        className="relative z-10 grid grid-cols-1 lg:grid-cols-2 items-center gap-10 lg:gap-14"
        style={{ padding: '40px 24px 60px', maxWidth: '1280px', margin: '0 auto' }}
      >
        {/* Left — copy */}
        <div>
          <div
            className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-white border border-[#E2E1DB] rounded-full text-[12.5px] font-medium text-[#3D3D38] mb-7"
            style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.06)' }}
          >
            <span className="relative flex w-2 h-2">
              <span className="absolute inline-flex w-full h-full rounded-full bg-[#2563EB] opacity-40 animate-ping" />
              <span className="relative flex w-2 h-2 rounded-full bg-[#2563EB]" />
            </span>
            Built for Yaoundé drivers
          </div>

          <h1
            className="font-bold text-[#111210] leading-none mb-5"
            style={{ fontFamily: 'Georgia, serif', fontSize: 'clamp(40px, 8vw, 68px)', letterSpacing: '-1.5px' }}
          >
            Navigate<br />
            <span className="font-light italic text-[#7A7A72]">smarter.</span><br />
            Drive safer.
          </h1>

          <p className="text-[16px] text-[#7A7A72] leading-relaxed mb-9 max-w-sm">
            Real-time traffic predictions, community incident reports, and automatic proximity alerts — all in one clean interface built for Yaoundé roads.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/register"
              className="px-7 py-3 rounded-xl text-[15px] font-semibold text-white bg-[#111210] hover:bg-[#1c1e1b] transition-colors"
              style={{ boxShadow: '0 2px 8px rgba(17,18,16,0.28)' }}
            >
              Create free account
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 rounded-xl text-[15px] font-medium text-[#3D3D38] border border-[#C8C7BF] hover:bg-white hover:border-[#B0AFA7] transition-colors"
            >
              Log in
            </Link>
          </div>
        </div>

        {/* Right — map card */}
        <div>
          <MapIllustration />
        </div>
      </div>
    </section>
  );
}

function StatsBar() {
  const stats = [
    { value: '12,000+',   label: 'Registered drivers' },
    { value: '5 km',      label: 'Proximity alert radius' },
    { value: '4 levels',  label: 'Congestion accuracy' },
    { value: 'Real‑time', label: 'Incident reporting & alerts' },
  ];
  return (
    <section className="grid grid-cols-2 lg:grid-cols-4 bg-white border-y border-[#E2E1DB]">
      {stats.map((stat, i) => (
        <div
          key={i}
          className={`flex flex-col items-center justify-center py-8 text-center hover:bg-[#F7F6F2] transition-colors
            ${i % 2 !== 1 ? 'border-r border-[#E2E1DB]' : ''}
            ${i < 2 ? 'border-b lg:border-b-0 border-[#E2E1DB]' : ''}
            lg:border-r lg:last:border-r-0
          `}
        >
          <span
            className="text-[32px] lg:text-[38px] font-bold text-[#111210] leading-none mb-1.5"
            style={{ fontFamily: 'Georgia, serif', letterSpacing: '-1px' }}
          >
            {stat.value}
          </span>
          <span className="text-[12px] lg:text-[13px] text-[#7A7A72] px-2">{stat.label}</span>
        </div>
      ))}
    </section>
  );
}

function FeaturesSection() {
  const features = [
    {
      icon: '📍',
      name: 'Proximity alerts',
      description: "Get notified the moment an incident, roadblock, or hazard enters your 5 km radius — before you reach it.",
    },
    {
      icon: '📡',
      name: 'Live predictions',
      description: "AI-powered congestion forecasts updated every 30 seconds, tailored to Yaoundé's road patterns.",
    },
    {
      icon: '🤝',
      name: 'Community reports',
      description: "Drivers on the ground share what's happening in real time — potholes, accidents, police checkpoints, and more.",
    },
  ];
  return (
    <section id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-[#F7F6F2]" style={{ padding: '60px 24px' }}>
      {features.map((f, i) => (
        <div
          key={i}
          className="bg-white border border-[#E2E1DB] rounded-2xl p-7 hover:-translate-y-1 hover:border-[#C8C7BF] transition-all duration-200"
          style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.06)' }}
        >
          <div className="w-10 h-10 flex items-center justify-center bg-[#EFEDE7] border border-[#E2E1DB] rounded-xl text-lg mb-5">
            {f.icon}
          </div>
          <h3
            className="text-[18px] font-semibold text-[#111210] mb-2.5"
            style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.3px' }}
          >
            {f.name}
          </h3>
          <p className="text-[14px] text-[#7A7A72] leading-relaxed">{f.description}</p>
        </div>
      ))}
    </section>
  );
}

function HowItWorksSection() {
  const steps = [
    { number: '01', title: 'Create account',   description: 'Sign up free in under a minute. No payment, no spam, ever.' },
    { number: '02', title: 'Enter your route', description: 'Type your origin and destination. Pick your time and day.' },
    { number: '03', title: 'Get predictions',  description: 'See congestion level per segment and the best departure time.' },
    { number: '04', title: 'Stay informed',    description: 'Receive live alerts for incidents within 5 km as you drive.' },
  ];
  return (
    <section id="how-it-works" className="bg-white border-y border-[#E2E1DB]" style={{ padding: '72px 24px' }}>
      <div className="text-[12px] font-semibold tracking-widest uppercase text-[#2563EB] mb-3.5">Process</div>
      <h2
        className="font-bold text-[#111210] mb-3"
        style={{ fontFamily: 'Georgia, serif', fontSize: 'clamp(28px, 4vw, 44px)', letterSpacing: '-0.8px' }}
      >
        Up and running in four steps.
      </h2>
      <p className="text-[15px] text-[#7A7A72] mb-12 max-w-md">
        No complicated setup. Just sign up, enter your route, and let UrbanFlow do the rest.
      </p>

      {/* Desktop: 4-column with horizontal connector line */}
      <div className="hidden md:grid grid-cols-4 relative">
        <div
          className="absolute border-t border-[#C8C7BF]"
          style={{ top: '22px', left: 'calc(12.5% + 22px)', right: 'calc(12.5% + 22px)', zIndex: 0 }}
        />
        {steps.map((step, i) => (
          <div key={i} className="flex flex-col items-center text-center px-5 relative" style={{ zIndex: 1 }}>
            <div
              className="w-11 h-11 rounded-full bg-[#111210] text-white flex items-center justify-center text-[13px] font-semibold mb-5 flex-shrink-0"
              style={{ boxShadow: '0 4px 12px rgba(17,18,16,0.08)' }}
            >
              {step.number}
            </div>
            <div className="text-[15px] font-semibold text-[#111210] mb-2">{step.title}</div>
            <p className="text-[13.5px] text-[#7A7A72] leading-relaxed">{step.description}</p>
          </div>
        ))}
      </div>

      {/* Mobile: vertical stepper */}
      <div className="flex flex-col gap-0 md:hidden">
        {steps.map((step, i) => (
          <div key={i} className="flex gap-5">
            {/* Left: number + vertical line */}
            <div className="flex flex-col items-center flex-shrink-0">
              <div
                className="w-11 h-11 rounded-full bg-[#111210] text-white flex items-center justify-center text-[13px] font-semibold flex-shrink-0"
                style={{ boxShadow: '0 4px 12px rgba(17,18,16,0.08)' }}
              >
                {step.number}
              </div>
              {i < steps.length - 1 && (
                <div className="w-px flex-1 bg-[#C8C7BF] my-2" style={{ minHeight: '32px' }} />
              )}
            </div>
            {/* Right: text */}
            <div className="pb-8">
              <div className="text-[15px] font-semibold text-[#111210] mb-1.5 mt-2.5">{step.title}</div>
              <p className="text-[13.5px] text-[#7A7A72] leading-relaxed">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReviewsSection() {
  const reviews = [
    {
      text: "I drive Bastos to Melen every morning. Since using UrbanFlow I've cut 25 minutes off my commute. The congestion predictions are eerily accurate — it warned me about the Nlongkak jam before I even got close.",
      highlight: "cut 25 minutes off my commute",
      name: 'Emmanuel Kamga',
      role: 'Sales rep · Bastos',
      initials: 'EK',
      avatarBg: '#EEF3FD', avatarColor: '#2563EB',
      featured: true,
    },
    {
      text: "The community incident reports are what sets this apart. Someone flagged a checkpoint on Carrefour Warda and I was notified before I even left my house. This app genuinely understands how we drive here.",
      highlight: "before I even left my house",
      name: 'Astride Ngo Biyong',
      role: 'Teacher · Biyem-Assi',
      initials: 'AN',
      avatarBg: '#FEF3C7', avatarColor: '#92400E',
      featured: false,
    },
    {
      text: "Clean, fast, and it actually works for Yaoundé — not just copy-pasted from some foreign city. The proximity alerts have saved me from two accidents I didn't see coming. Highly recommended.",
      highlight: "saved me from two accidents",
      name: 'Patrick Mvondo',
      role: 'Delivery driver · Melen',
      initials: 'PM',
      avatarBg: '#F0FDF4', avatarColor: '#166534',
      featured: false,
    },
  ];

  return (
    <section className="bg-[#F7F6F2]" style={{ padding: '72px 24px' }}>
      <div className="text-[12px] font-semibold tracking-widest uppercase text-[#2563EB] mb-3.5">Testimonials</div>
      <h2
        className="font-bold text-[#111210] mb-3"
        style={{ fontFamily: 'Georgia, serif', fontSize: 'clamp(28px, 4vw, 44px)', letterSpacing: '-0.8px' }}
      >
        Trusted by Yaoundé drivers.
      </h2>
      <p className="text-[15px] text-[#7A7A72] mb-10 max-w-md">
        Over 12,000 drivers use UrbanFlow every day to beat traffic on Yaoundé's roads.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {reviews.map((r, i) => (
          <div
            key={i}
            className={`bg-white rounded-2xl p-7 flex flex-col gap-4 hover:-translate-y-0.5 transition-all duration-200 ${r.featured ? 'border-2 border-[#111210]' : 'border border-[#E2E1DB]'}`}
            style={{ boxShadow: r.featured ? '0 4px 12px rgba(17,18,16,0.08)' : '0 1px 3px rgba(17,18,16,0.06)' }}
          >
            <div className="text-amber-400 text-[13px] tracking-widest">★★★★★</div>
            <p className="text-[14.5px] text-[#3D3D38] leading-relaxed flex-1">
              {r.text.split(r.highlight).map((part, j, arr) => (
                j < arr.length - 1
                  ? <span key={j}>{part}<strong className="text-[#111210] font-semibold">{r.highlight}</strong></span>
                  : <span key={j}>{part}</span>
              ))}
            </p>
            <div className="flex items-center gap-3 pt-4 border-t border-[#E2E1DB]">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-[13px] font-semibold flex-shrink-0"
                style={{ backgroundColor: r.avatarBg, color: r.avatarColor }}
              >
                {r.initials}
              </div>
              <div>
                <div className="text-[13.5px] font-semibold text-[#111210]">{r.name}</div>
                <div className="text-[12px] text-[#7A7A72]">{r.role}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTABanner() {
  return (
    <section
      className="bg-[#111210] flex flex-col md:flex-row items-start md:items-center justify-between gap-8"
      style={{ padding: '60px 24px' }}
    >
      <div className="max-w-xl">
        <h2
          className="font-bold text-white mb-3"
          style={{ fontFamily: 'Georgia, serif', fontSize: 'clamp(26px, 4vw, 40px)', letterSpacing: '-0.8px' }}
        >
          Ready to drive smarter?
        </h2>
        <p className="text-[15px] text-white/50 leading-relaxed">
          Join thousands of Yaoundé drivers already using UrbanFlow to beat traffic every day. Free to get started — always.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3 flex-shrink-0">
        <Link
          to="/register"
          className="px-7 py-3 rounded-xl text-[15px] font-semibold text-[#111210] bg-white hover:bg-[#F0EFE9] transition-colors whitespace-nowrap"
        >
          Create free account
        </Link>
        <Link
          to="/login"
          className="px-6 py-3 rounded-xl text-[15px] font-medium text-white/70 border border-white/20 hover:border-white/50 hover:text-white transition-colors whitespace-nowrap"
        >
          Log in
        </Link>
      </div>
    </section>
  );
}

function Footer() {
  const productLinks = ['How it works', 'Features', 'Pricing', 'Changelog'];
  const companyLinks = ['About us', 'Blog', 'Careers', 'Contact'];
  const legalLinks   = ['Privacy policy', 'Terms of service', 'Cookie policy'];

  return (
    <footer className="bg-[#111210] border-t border-white/5" style={{ padding: '52px 24px 32px' }}>
      {/* Top grid: brand col + 3 link columns */}
      <div
        className="grid gap-10 mb-10"
        style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}
      >
        {/* Brand */}
        <div className="col-span-full sm:col-span-1" style={{ gridColumn: 'span 1' }}>
          <span className="text-[18px] font-bold" style={{ fontFamily: 'Georgia, serif' }}>
            <span className="text-white">Urban</span>
            <span className="text-[#6B9FFF]">Flow</span>
          </span>
          <p className="text-[13.5px] text-white/35 leading-relaxed mt-3.5 max-w-[220px]">
            Real-time traffic intelligence built specifically for the roads of Yaoundé, Cameroon.
          </p>
          <div className="flex gap-2.5 mt-5">
            {['𝕏', 'f', 'W', 'in'].map((s, i) => (
              <a
                key={i} href="#"
                className="w-8 h-8 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center text-[13px] text-white/45 hover:bg-white/10 hover:border-white/25 hover:text-white transition-colors"
              >
                {s}
              </a>
            ))}
          </div>
        </div>

        <div>
          <div className="text-[12px] font-semibold tracking-widest uppercase text-white/30 mb-4">Product</div>
          <ul className="flex flex-col gap-2.5">
            {productLinks.map((l) => (
              <li key={l}><a href="#" className="text-[13.5px] text-white/50 hover:text-white transition-colors">{l}</a></li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-[12px] font-semibold tracking-widest uppercase text-white/30 mb-4">Company</div>
          <ul className="flex flex-col gap-2.5">
            {companyLinks.map((l) => (
              <li key={l}><a href="#" className="text-[13.5px] text-white/50 hover:text-white transition-colors">{l}</a></li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-[12px] font-semibold tracking-widest uppercase text-white/30 mb-4">Legal</div>
          <ul className="flex flex-col gap-2.5">
            {legalLinks.map((l) => (
              <li key={l}><a href="#" className="text-[13.5px] text-white/50 hover:text-white transition-colors">{l}</a></li>
            ))}
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-6 border-t border-white/5">
        <span className="text-[13px] text-white/25">© 2026 UrbanFlow · SEN3244 · Made in Yaoundé 🇨🇲</span>
        <div className="flex gap-5">
          {['Privacy', 'Terms', 'Cookies'].map((l) => (
            <a key={l} href="#" className="text-[13px] text-white/35 hover:text-white/70 transition-colors">{l}</a>
          ))}
        </div>
      </div>
    </footer>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      <main className="flex-1">
        <HeroSection />
        <StatsBar />
        <FeaturesSection />
        <HowItWorksSection />
        <ReviewsSection />
        <CTABanner />
      </main>
      <Footer />
    </div>
  );
}