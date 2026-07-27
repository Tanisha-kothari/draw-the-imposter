import { useEffect, useState } from 'react';
import clsx from 'clsx';

interface CountdownTimerProps {
  timeRemaining: number;
  totalTime: number;
  onComplete?: () => void;
  size?: 'sm' | 'md' | 'lg';
}

export default function CountdownTimer({ timeRemaining, totalTime, onComplete, size = 'md' }: CountdownTimerProps) {
  const [prevTime, setPrevTime] = useState(timeRemaining);
  const percentage = totalTime > 0 ? (timeRemaining / totalTime) * 100 : 0;
  const isUrgent = timeRemaining <= 10;
  const isCritical = timeRemaining <= 5;

  useEffect(() => {
    if (timeRemaining <= 0 && prevTime > 0) {
      onComplete?.();
    }
    setPrevTime(timeRemaining);
  }, [timeRemaining, prevTime, onComplete]);

  const sizeClasses = {
    sm: 'w-16 h-16 text-lg',
    md: 'w-24 h-24 text-3xl',
    lg: 'w-32 h-32 text-4xl',
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={clsx(
          'relative rounded-full flex items-center justify-center font-bold transition-all duration-500',
          sizeClasses[size],
          isCritical ? 'text-red-400' : isUrgent ? 'text-yellow-400' : 'text-white'
        )}
      >
        {/* Circular progress */}
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            strokeLinecap="round"
            className="text-gray-700"
          />
          <circle
            cx="50" cy="50" r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 45}`}
            strokeDashoffset={`${2 * Math.PI * 45 * (1 - percentage / 100)}`}
            className={isCritical ? 'text-red-500' : isUrgent ? 'text-yellow-500' : 'text-primary-500'}
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
        <span className="relative">{timeRemaining}</span>
      </div>
    </div>
  );
}
