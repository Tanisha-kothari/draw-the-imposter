export default function LoadingScreen({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-gray-950 gap-4">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 border-4 border-primary-500/20 rounded-full" />
        <div className="absolute inset-0 border-4 border-transparent border-t-primary-500 rounded-full animate-spin" />
      </div>
      <p className="text-gray-400 text-sm animate-pulse">{message}</p>
    </div>
  );
}
