/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls to the FastAPI backend in dev so the browser hits same-origin.
  async rewrites() {
    const api = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default nextConfig;
