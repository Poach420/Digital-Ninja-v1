import React from 'react';

const BrandLogo = ({ className = 'h-8 w-8' }) => {
  return (
    <picture>
      {/* Prefer user-provided PNG if present */}
      <source srcSet="/digital-ninja-logo.png" type="image/png" />
      {/* Fallback SVG we bundle so branding always shows */}
      <img
        src="/digital-ninja-logo-fallback.svg"
        alt="Digital Ninja"
        className={className}
        referrerPolicy="no-referrer"
      />
    </picture>
  );
};

export default BrandLogo;