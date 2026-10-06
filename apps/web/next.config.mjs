/** @type {import('next').NextConfig} */
const isCapacitor = process.env.BUILD_FOR_CAPACITOR === 'true';

const nextConfig = {
  reactStrictMode: true,
  output: isCapacitor ? 'export' : 'standalone',
  distDir: isCapacitor ? 'dist' : '.next',
  images: {
    unoptimized: isCapacitor,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.aliyuncs.com',
      },
    ],
  },
};

export default nextConfig;
