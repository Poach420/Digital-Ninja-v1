import React, { useEffect, useState } from 'react';

// Professional ninja-themed SVG logo
const NinjaLogo = ({ className }) => (
  <svg className={className} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="ninjaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#9b00e8"/>
        <stop offset="100%" stopColor="#ff4500"/>
      </linearGradient>
    </defs>
    {/* Background circle */}
    <circle cx="50" cy="50" r="48" fill="url(#ninjaGrad)"/>
    {/* Ninja face/mask */}
    <ellipse cx="50" cy="45" rx="30" ry="25" fill="#1a1a2e"/>
    {/* Eyes */}
    <ellipse cx="38" cy="42" rx="8" ry="4" fill="#fff"/>
    <ellipse cx="62" cy="42" rx="8" ry="4" fill="#fff"/>
    <circle cx="40" cy="42" r="2" fill="#0f0f1a"/>
    <circle cx="64" cy="42" r="2" fill="#0f0f1a"/>
    {/* Headband */}
    <rect x="15" y="32" width="70" height="8" rx="2" fill="#ff4500"/>
    <path d="M75 36 L90 28 L88 38 L75 36" fill="#ff4500"/>
    <path d="M75 36 L90 44 L88 34 L75 36" fill="#cc3700"/>
    {/* Mask bottom */}
    <path d="M25 50 Q50 70 75 50 L75 55 Q50 75 25 55 Z" fill="#1a1a2e"/>
  </svg>
);

const BrandLogo = ({ className = 'h-10 w-10' }) => {
  const [usePng, setUsePng] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setUsePng(true);
    img.onerror = () => setUsePng(false);
    img.src = '/digital-ninja-logo.png';
  }, []);

  if (usePng) {
    return <img src="/digital-ninja-logo.png" alt="Digital Ninja" className={className} />;
  }

  return <NinjaLogo className={className} />;
};

export default BrandLogo;