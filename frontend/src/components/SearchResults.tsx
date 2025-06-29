import { motion } from 'framer-motion';
import { Star, Hash, Clock, Zap } from 'lucide-react';
import { cn } from '../utils/cn';

interface SearchResult {
  image_id: string;
  score: number;
  metadata?: Record<string, any>;
}

interface SearchResultsProps {
  results: {
    query_id: string;
    results: SearchResult[];
    total_found: number;
    search_time_ms: number;
    cached: boolean;
  };
}

export default function SearchResults({ results }: SearchResultsProps) {
  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'from-green-500 to-emerald-500';
    if (score >= 0.7) return 'from-yellow-500 to-amber-500';
    if (score >= 0.5) return 'from-orange-500 to-red-500';
    return 'from-gray-500 to-gray-600';
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 0.9) return '🎯';
    if (score >= 0.7) return '✨';
    if (score >= 0.5) return '👍';
    return '🤔';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-6xl mx-auto"
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-pink-600/10 backdrop-blur-xl rounded-xl p-4 mb-4 border border-white/20 dark:border-gray-700/50"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Search Results
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Found {results.total_found} similar images
            </p>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="flex items-center space-x-1 px-3 py-1.5 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm rounded-lg"
            >
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">
                {results.search_time_ms.toFixed(0)}ms
              </span>
            </motion.div>
            
            {results.cached && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                whileHover={{ scale: 1.05 }}
                className="flex items-center space-x-1 px-3 py-1.5 bg-green-500/20 backdrop-blur-sm rounded-lg"
              >
                <Zap className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  Cached
                </span>
              </motion.div>
            )}
            
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="flex items-center space-x-1 px-3 py-1.5 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm rounded-lg"
            >
              <Hash className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {results.query_id.slice(0, 8)}...
              </span>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {results.results.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
            <Star className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No similar images found
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            Try uploading a different image or adjusting the similarity threshold
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.results.map((result, index) => (
            <motion.div
              key={`${result.image_id}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -5 }}
              className="group relative"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="relative bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl rounded-xl p-4 border border-white/20 dark:border-gray-700/50 hover:border-white/40 dark:hover:border-gray-600/50 transition-all">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate pr-2">
                    {result.image_id}
                  </h3>
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    className="flex items-center space-x-1"
                  >
                    <span className="text-xl">{getScoreEmoji(result.score)}</span>
                    <span className={cn(
                      "text-sm font-bold px-2 py-1 rounded-lg",
                      "bg-gradient-to-r text-white",
                      getScoreColor(result.score)
                    )}>
                      {(result.score * 100).toFixed(1)}%
                    </span>
                  </motion.div>
                </div>

                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Similarity</span>
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {result.score.toFixed(3)}
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${result.score * 100}%` }}
                      transition={{ delay: index * 0.05 + 0.3, duration: 0.5 }}
                      className={cn(
                        "h-full rounded-full bg-gradient-to-r",
                        getScoreColor(result.score)
                      )}
                    />
                  </div>
                </div>

                {result.metadata && Object.keys(result.metadata).length > 0 && (
                  <div className="space-y-1.5 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Metadata
                    </p>
                    {Object.entries(result.metadata).slice(0, 3).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400 capitalize">
                          {key}
                        </span>
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                          {typeof value === 'object' ? 
                            JSON.stringify(value) : 
                            String(value)
                          }
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}