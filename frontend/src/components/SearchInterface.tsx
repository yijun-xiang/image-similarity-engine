import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Search, Image, X, Loader2, Sparkles } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { searchImages, indexImage } from '../services/api';
import SearchResults from './SearchResults';
import { cn } from '../utils/cn';

interface SearchInterfaceProps {
  className?: string;
}

export default function SearchInterface({ className }: SearchInterfaceProps) {
  const [mode, setMode] = useState<'search' | 'index'>('search');
  const [preview, setPreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [searchResults, setSearchResults] = useState<any>(null);
  const [imageId, setImageId] = useState('');
  const [tags, setTags] = useState('');

  const searchMutation = useMutation({
    mutationFn: (imageData: string) => searchImages(imageData),
    onSuccess: (data) => {
      setSearchResults(data);
      toast.success(`Found ${data.total_found} similar images in ${data.search_time_ms.toFixed(0)}ms`);
    },
    onError: () => {
      toast.error('Search failed. Please try again.');
    },
  });

  const indexMutation = useMutation({
    mutationFn: ({ imageData, imageId, metadata }: any) => 
      indexImage(imageData, imageId, metadata),
    onSuccess: (data) => {
      toast.success(`Image indexed successfully in ${data.processing_time_ms.toFixed(0)}ms`);
      resetForm();
    },
    onError: () => {
      toast.error('Indexing failed. Please try again.');
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        setPreview(result);
        
        if (mode === 'search') {
          const base64Data = result.split(',')[1];
          searchMutation.mutate(base64Data);
        }
      };
      reader.readAsDataURL(file);
    }
  }, [mode, searchMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    multiple: false,
  });

  const handleIndex = () => {
    if (!preview) return;
    
    const base64Data = preview.split(',')[1];
    const metadata = tags.split(',').map(tag => tag.trim()).filter(Boolean);
    
    indexMutation.mutate({
      imageData: base64Data,
      imageId: imageId || undefined,
      metadata: { tags: metadata },
    });
  };

  const resetForm = () => {
    setPreview(null);
    setImageFile(null);
    setSearchResults(null);
    setImageId('');
    setTags('');
  };

  const isLoading = searchMutation.isPending || indexMutation.isPending;

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex justify-center">
        <motion.div
          layout
          className="bg-white/10 dark:bg-gray-900/50 backdrop-blur-xl rounded-xl p-1 border border-white/20 dark:border-gray-700/50"
        >
          <div className="flex space-x-1">
            {[
              { value: 'search', label: 'Search Images', icon: Search },
              { value: 'index', label: 'Index New Image', icon: Upload },
            ].map((option) => (
              <motion.button
                key={option.value}
                onClick={() => {
                  setMode(option.value as any);
                  resetForm();
                }}
                className={cn(
                  "relative px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300",
                  "flex items-center space-x-2",
                  mode === option.value
                    ? "text-white"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {mode === option.value && (
                  <motion.div
                    layoutId="activeMode"
                    className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <option.icon className="relative z-10 h-4 w-4" />
                <span className="relative z-10">{option.label}</span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div
        layout
        className="max-w-3xl mx-auto"
      >
        <div
          {...getRootProps()}
          className={cn(
            "relative group cursor-pointer",
            "rounded-2xl transition-all duration-500",
            "bg-white/10 dark:bg-gray-900/50 backdrop-blur-xl",
            "border-2 border-dashed",
            isDragActive
              ? "border-blue-500 bg-blue-500/10 scale-[1.02]"
              : "border-gray-300/50 dark:border-gray-700/50 hover:border-gray-400 dark:hover:border-gray-600",
            isLoading && "pointer-events-none opacity-50"
          )}
        >
          <input {...getInputProps()} />
          
          <div className="p-10">
            <AnimatePresence mode="wait">
              {preview ? (
                <motion.div
                  key="preview"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="space-y-4"
                >
                  <div className="relative max-w-md mx-auto">
                    <img
                      src={preview}
                      alt="Preview"
                      className="rounded-xl shadow-xl w-full max-h-64 object-contain"
                    />
                    {!isLoading && (
                      <motion.button
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          resetForm();
                        }}
                        className="absolute -top-2 -right-2 p-2 bg-red-500 text-white rounded-full shadow-lg hover:bg-red-600 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </motion.button>
                    )}
                  </div>
                  
                  {imageFile && (
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {imageFile.name} ({(imageFile.size / 1024 / 1024).toFixed(2)} MB)
                      </p>
                    </div>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="text-center space-y-4"
                >
                  <div className="relative">
                    <motion.div
                      animate={{
                        scale: isDragActive ? 1.2 : 1,
                        rotate: isDragActive ? 180 : 0,
                      }}
                      transition={{ duration: 0.5 }}
                      className="relative inline-block"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full blur-2xl opacity-30 group-hover:opacity-50 transition-opacity" />
                      <div className="relative p-6 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full">
                        {isDragActive ? (
                          <Sparkles className="h-12 w-12 text-blue-500" />
                        ) : (
                          <Image className="h-12 w-12 text-gray-500 dark:text-gray-400" />
                        )}
                      </div>
                    </motion.div>
                  </div>
                  
                  <div>
                    <p className="text-xl font-semibold text-gray-700 dark:text-gray-300">
                      {isDragActive ? 'Drop your image here' : 'Drag & drop an image'}
                    </p>
                    <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                      or click to browse (JPEG, PNG, GIF, WebP)
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl flex items-center justify-center"
              >
                <div className="text-center space-y-3">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto" />
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {mode === 'search' ? 'Searching...' : 'Indexing...'}
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {mode === 'index' && preview && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 space-y-3"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Image ID (optional)
                </label>
                <input
                  type="text"
                  value={imageId}
                  onChange={(e) => setImageId(e.target.value)}
                  className="w-full px-4 py-2.5 text-sm bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm border border-gray-300/50 dark:border-gray-700/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="auto-generated if empty"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-4 py-2.5 text-sm bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm border border-gray-300/50 dark:border-gray-700/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="nature, landscape, sunset"
                />
              </div>
            </div>
            
            <motion.button
              onClick={handleIndex}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all flex items-center justify-center space-x-2"
            >
              <Upload className="h-5 w-5" />
              <span>Index Image</span>
            </motion.button>
          </motion.div>
        )}
      </motion.div>

      <AnimatePresence>
        {searchResults && mode === 'search' && (
          <SearchResults results={searchResults} />
        )}
      </AnimatePresence>
    </div>
  );
}