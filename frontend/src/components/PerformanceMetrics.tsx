import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Gauge, Timer, Target } from 'lucide-react';

const metrics = [
  {
    label: 'Throughput',
    value: '94+',
    unit: 'req/s',
    icon: TrendingUp,
    color: 'from-blue-500 to-cyan-500',
    description: 'Requests per second',
  },
  {
    label: 'Latency',
    value: '105',
    unit: 'ms',
    icon: Timer,
    color: 'from-green-500 to-emerald-500',
    description: 'Average response time',
  },
  {
    label: 'P95 Latency',
    value: '476',
    unit: 'ms',
    icon: Gauge,
    color: 'from-purple-500 to-pink-500',
    description: '95th percentile',
  },
  {
    label: 'Accuracy',
    value: '100',
    unit: '%',
    icon: Target,
    color: 'from-orange-500 to-red-500',
    description: 'Perfect similarity match',
  },
];

export default function PerformanceMetrics() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="mt-12"
    >
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Performance Metrics
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Real-world benchmarks on Apple Silicon with MPS acceleration
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            whileHover={{ y: -5 }}
            className="relative group"
          >
            <div className={`absolute inset-0 bg-gradient-to-r ${metric.color} rounded-2xl blur-xl opacity-30 group-hover:opacity-50 transition-opacity`} />
            
            <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6 border border-white/20 dark:border-gray-700/50 text-center">
              <div className={`inline-flex p-3 bg-gradient-to-r ${metric.color} rounded-xl mb-4`}>
                <metric.icon className="h-6 w-6 text-white" />
              </div>
              
              <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                {metric.label}
              </h4>
              
              <div className="flex items-baseline justify-center mb-2">
                <span className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metric.value}
                </span>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400 ml-1">
                  {metric.unit}
                </span>
              </div>
              
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {metric.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
