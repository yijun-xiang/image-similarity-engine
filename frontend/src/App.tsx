import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { Moon, Sun, Sparkles, Cpu, Database, Zap } from 'lucide-react';
import SearchInterface from './components/SearchInterface';
import SystemMonitor from './components/SystemMonitor';
import PerformanceMetrics from './components/PerformanceMetrics';
import BackgroundAnimation from './components/BackgroundAnimation';
import { useThemeStore } from './stores/themeStore';

const queryClient = new QueryClient();

function App() {
  const { isDark, toggleTheme } = useThemeStore();
  const [activeView, setActiveView] = useState<'search' | 'monitor'>('search');

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen transition-colors duration-500 ${
        isDark ? 'bg-gray-950' : 'bg-gray-50'
      }`}>
        <BackgroundAnimation />
        
        <motion.header
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="relative z-50"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-pink-600/10 backdrop-blur-xl" />
          <div className="relative container mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <motion.div 
                className="flex items-center space-x-4"
                whileHover={{ scale: 1.02 }}
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur-lg opacity-75" />
                  <div className="relative bg-black/90 p-3 rounded-xl">
                    <Sparkles className="h-8 w-8 text-white" />
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Image Similarity Engine
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Scalable ML-powered search system
                  </p>
                </div>
              </motion.div>

              <div className="flex items-center space-x-6">
                <div className="flex bg-black/10 dark:bg-white/10 rounded-lg p-1 backdrop-blur-sm">
                  <button
                    onClick={() => setActiveView('search')}
                    className={`px-4 py-2 rounded-md transition-all duration-300 ${
                      activeView === 'search'
                        ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-lg'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    Search
                  </button>
                  <button
                    onClick={() => setActiveView('monitor')}
                    className={`px-4 py-2 rounded-md transition-all duration-300 ${
                      activeView === 'monitor'
                        ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-lg'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    Monitor
                  </button>
                </div>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={toggleTheme}
                  className="p-3 bg-black/10 dark:bg-white/10 rounded-lg backdrop-blur-sm hover:bg-black/20 dark:hover:bg-white/20 transition-colors"
                >
                  <AnimatePresence mode="wait">
                    {isDark ? (
                      <motion.div
                        key="moon"
                        initial={{ rotate: -90, opacity: 0 }}
                        animate={{ rotate: 0, opacity: 1 }}
                        exit={{ rotate: 90, opacity: 0 }}
                      >
                        <Moon className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="sun"
                        initial={{ rotate: 90, opacity: 0 }}
                        animate={{ rotate: 0, opacity: 1 }}
                        exit={{ rotate: -90, opacity: 0 }}
                      >
                        <Sun className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>
              </div>
            </div>
          </div>
        </motion.header>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="container mx-auto px-6 mt-4 mb-8"
        >
          <div className="flex flex-wrap gap-3 justify-center">
            {[
              { icon: Cpu, label: 'CLIP ViT-B/32', color: 'from-blue-500 to-cyan-500' },
              { icon: Database, label: 'Qdrant Vector DB', color: 'from-purple-500 to-pink-500' },
              { icon: Zap, label: 'FastAPI + Redis', color: 'from-orange-500 to-red-500' },
            ].map((tech, i) => (
              <motion.div
                key={tech.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                whileHover={{ scale: 1.05 }}
                className="relative group"
              >
                <div className={`absolute inset-0 bg-gradient-to-r ${tech.color} rounded-full blur-md opacity-50 group-hover:opacity-75 transition-opacity`} />
                <div className="relative flex items-center space-x-2 px-4 py-2 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-full border border-white/20 dark:border-gray-700/50">
                  <tech.icon className="h-4 w-4 text-gray-700 dark:text-gray-300" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {tech.label}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <main className="container mx-auto px-6 pb-12">
          <AnimatePresence mode="wait">
            {activeView === 'search' ? (
              <motion.div
                key="search"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <SearchInterface />
                <PerformanceMetrics />
              </motion.div>
            ) : (
              <motion.div
                key="monitor"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <SystemMonitor />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <Toaster
          position="bottom-right"
          toastOptions={{
            className: 'dark:bg-gray-800 dark:text-white',
            duration: 4000,
          }}
        />
      </div>
    </QueryClientProvider>
  );
}

export default App;
