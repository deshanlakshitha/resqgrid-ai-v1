/** @type {import('next').NextConfig} */
const isCapacitor = process.env.BUILD_FOR_CAPACITOR === 'true';
const isDevelopment = process.env.NODE_ENV === 'development';
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').origin;
const mapOrigin = new URL(process.env.NEXT_PUBLIC_MAP_STYLE_URL || 'https://tiles.openfreemap.org/styles/liberty').origin;
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' ${isDevelopment ? "'unsafe-eval'" : ''} https://maps.googleapis.com https://maps.gstatic.com`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  `img-src 'self' data: blob: ${mapOrigin} https://*.googleapis.com https://*.gstatic.com https://*.google.com`,
  `connect-src 'self' ${apiOrigin} ${mapOrigin} https://tiles.openfreemap.org https://nominatim.openstreetmap.org https://*.googleapis.com https://*.gstatic.com https://*.google.com ${isDevelopment ? 'ws://localhost:*' : ''}`,
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join('; ');

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  ...(isCapacitor ? {} : {
    async headers() {
      return [{ source: '/:path*', headers: [
        { key: 'Content-Security-Policy', value: csp },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(self)' },
        { key: 'Strict-Transport-Security', value: 'max-age=31536000' },
      ] }];
    },
  }),
  output: isCapacitor ? 'export' : 'standalone',
  distDir: isCapacitor ? 'dist' : '.next',
  trailingSlash: isCapacitor,
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.aliyuncs.com',
      },
    ],
  },
};

export default nextConfig;
