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
  // Add custom error handling for 404 errors
  onDemandEntries: {
    // Period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 60 * 1000,
    // Number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 5,
  },
  // Ensure static files are properly served
  async rewrites() {
    return [
      {
        source: '/results/:path*',
        destination: '/api/proxy/results/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: '/uploads/:path*',
      },
      {
        source: '/logos/:path*',
        destination: '/logos/:path*',
      },
    ]
  },
  // Add public directory configuration
  publicRuntimeConfig: {
    staticFolder: '/public',
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
