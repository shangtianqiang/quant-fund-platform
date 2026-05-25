export function LoadingSpinner({ text = "加载中..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <div className="w-8 h-8 border-2 border-gray-200 border-t-blue-500 rounded-full animate-spin mb-3" />
      <span className="text-sm">{text}</span>
    </div>
  )
}

export function ErrorMessage({ text, onRetry }: { text: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <span className="text-sm mb-3">{text}</span>
      {onRetry && (
        <button onClick={onRetry} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          重试
        </button>
      )}
    </div>
  )
}
