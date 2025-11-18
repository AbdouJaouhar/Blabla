/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    serverActions: true,
    allowedDevOrigins: [
        "http://136.59.129.136:3000", // the IP shown in your screenshot
        "http://localhost:3000",
    ],
};

export default nextConfig;
