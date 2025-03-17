// No need to try importing a non-existent file
const userConfig = undefined

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
    
    // Add alias for @ to match tsconfig paths
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': '.'
    }
    
    return config
  }
}

if (userConfig) {
  Object.assign(nextConfig, userConfig)
}

export default nextConfig
