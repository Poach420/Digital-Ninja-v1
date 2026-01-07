import React, { useState } from 'react';

const BrandLogo = ({ className = 'h-8 w-8 rounded-md' }) => {
  const [src, setSrc] = useState('/digital-ninja-logo.png'); // user-provided PNG if available
  return (
    <img
      src={src}
      alt="Digital Ninja"
      className={className}
      onError={() => setSrc('/digital-ninja-logo-fallback.svg')}
    />
  );
};

export default BrandLogo;