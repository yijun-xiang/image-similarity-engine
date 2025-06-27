import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Activity, Database, MemoryStick, Server, Zap, CheckCircle, XCircle } from 'lucide-react';
import { getStats, getHealth } from '../services/api';
import { cn } from '../utils/cn';

export default function SystemMonitor() {
  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 5000,
  });

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 5000,
  });

  const getCacheHitRate = () => {
    if (!stats?.cache.keyspace_hits || !stats?.cache.keyspace_misses) return 0;
    const total = stats.cache.keyspace_hits + stats.cache.keyspace_misses;
    return ((stats.cache.keyspace_hits / total) * 100);
  };

  const serviceStatusData = health?.services ? 
    Object.entries(health.services).map(([service, status]) => ({
      service: service.replace('_', ' '),
      status,
      healthy: status === 'healthy',
    })) : [];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          whileHover={{ y: -5 }}
          className="relative group"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-cyan-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/20 rounded-xl">
                <Database className="h-6 w-6 text-blue-500" />
              </div>
              <span className={cn(
                "text-xs font-medium px-2 py-1 rounded-full",
                health?.status === 'healthy' 
                  ? "bg-green-500/20 text-green-700 dark:text-green-300"
                  : "bg-red-500/20 text-red-700 dark:text-red-300"
              )}>
                {health?.status || 'Unknown'}
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Images Indexed
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {stats?.collection.points_count || 0}
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{ y: -5 }}
          className="relative group"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-green-600/20 to-emerald-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-500/20 rounded-xl">
                <Zap className="h-6 w-6 text-green-500" />
              </div>
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Real-time
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Cache Hit Rate
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {getCacheHitRate().toFixed(1)}%
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          whileHover={{ y: -5 }}
          className="relative group"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-500/20 rounded-xl">
                <MemoryStick className="h-6 w-6 text-purple-500" />
              </div>
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Redis
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Memory Usage
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {stats?.cache.used_memory_human || '0B'}
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -5 }}
          className="relative group"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-orange-600/20 to-red-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-500/20 rounded-xl">
                <Activity className="h-6 w-6 text-orange-500" />
              </div>
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Total
              </span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
              API Requests
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {stats?.cache.total_commands_processed || 0}
            </p>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <Server className="h-5 w-5 mr-2" />
            Service Health
          </h3>
          <div className="space-y-4">
            {serviceStatusData.map((service, i) => (
              <motion.div
                key={service.service}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + i * 0.1 }}
                className="flex items-center justify-between p-4 bg-gray-50/50 dark:bg-gray-800/50 rounded-xl"
              >
                <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">
                  {service.service}
                </span>
                <div className="flex items-center space-x-2">
                  {service.healthy ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className={cn(
                    "text-sm font-medium px-3 py-1 rounded-full",
                    service.healthy
                      ? "bg-green-500/20 text-green-700 dark:text-green-300"
                      : "bg-red-500/20 text-red-700 dark:text-red-300"
                  )}>
                    {service.status}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <Database className="h-5 w-5 mr-2" />
            Vector Database
          </h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-xl p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Collection
                </p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {stats?.collection.name || 'N/A'}
                </p>
              </div>
              <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-xl p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Dimensions
                </p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {stats?.collection.vector_size || 0}
                </p>
              </div>
              <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-xl p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Distance
                </p>
                <p className="font-semibold text-gray-900 dark:text-white capitalize">
                  {stats?.collection.distance || 'N/A'}
                </p>
              </div>
              <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-xl p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Segments
                </p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {stats?.collection.segments_count || 0}
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Cache Performance</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Hits</span>
                  <span className="font-medium text-green-600 dark:text-green-400">
                    {stats?.cache.keyspace_hits || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Misses</span>
                  <span className="font-medium text-red-600 dark:text-red-400">
                    {stats?.cache.keyspace_misses || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="flex justify-center">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            refetchStats();
            refetchHealth();
          }}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all flex items-center space-x-2"
        >
          <Activity className="h-5 w-5" />
          <span>Refresh Stats</span>
        </motion.button>
      </div>
    </div>
  );
}
