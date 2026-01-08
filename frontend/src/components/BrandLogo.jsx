import React, { useEffect, useState } from 'react';

const InlineFallback = ({ className }) => (
  <svg className={className} viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Digital Ninja">
    <defs>
      <linearGradient id="gn" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#9b00e8"/>
        <stop offset="100%" stopColor="#ff4500"/>
      </linearGradient>
    </defs>
    <rect rx="20" ry="20" width="128" height="128" fill="url(#gn)"/>
    <g fill="#fff">
      <path d="M28 64c0-19.882 16.118-36 36-36s36 16.118 36 36-16.118 36-36 36S28 83.882 28 64zm18 0c0 9.941 8.059 18 18 18s18-8.059 18-18-8.059-18-18-18-18 8.059-18 18z" opacity="0.15"/>
      <path d="M38 52h52l-8 8H46l-8-8zM38 68h52l-8 8H46l-8-8z" opacity="0.35"/>
      <path d="M50 80l14-32 14 32H50z"/>
    </g>
  </svg>
);

const BrandLogo = ({ className = 'h-10 w-10 rounded-lg' }) => {
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

  // Inline fallback SVG ensures the logo always renders
  return <InlineFallback className={className} />;
};

export default BrandLogo;