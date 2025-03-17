let userConfig = undefined
try {
  userConfig = await import('./v0-user-next.config')
} catch (e) {
  // ignore error
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  output: 'standalone',
  experimental: {
    optimizePackageImports: ['@radix-ui/react-icons'],
  },
  webpack: (config) => {
    // Ensure proper module resolution
    config.resolve.modules = ['node_modules', '.']
    return config
  }
}

if (userConfig) {
  Object.assign(nextConfig, userConfig)
}

export default nextConfig
