import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    return [
      {
        source: "/(.*)", // applies to all routes
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self';",
              "img-src 'self' data: blob:;",
              "media-src 'self' blob:;",
              "connect-src 'self' ws: https://cdn.jsdelivr.net;",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline';",
              "style-src 'self' 'unsafe-inline';",
              "object-src 'none';",
            ].join(" "),

          },
        ],
      },
    ];
  },
};

export default nextConfig;
