import { AVATAR_COLORS } from '../../lib/constants';

interface AvatarProps {
  nickname: string;
  colorIndex?: number;
  size?: 'sm' | 'md' | 'lg';
  isReady?: boolean;
  isHost?: boolean;
  isImposter?: boolean;
}

const sizes = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-14 h-14 text-lg' };

export default function Avatar({ nickname, colorIndex = 0, size = 'md', isReady, isHost, isImposter }: AvatarProps) {
  const initial = nickname?.charAt(0)?.toUpperCase() || '?';
  const bgColor = AVATAR_COLORS[colorIndex % AVATAR_COLORS.length];

  return (
    <div className="relative inline-flex flex-col items-center">
      <div
        className={`${sizes[size]} rounded-full flex items-center justify-center font-bold text-white transition-all duration-300`}
        style={{ backgroundColor: bgColor }}
      >
        {initial}
      </div>
      {isHost && (
        <span className="absolute -top-1 -right-1 bg-yellow-500 text-black text-[10px] font-bold px-1 rounded-full leading-none">
          ★
        </span>
      )}
      {isReady !== undefined && (
        <span className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-900 ${isReady ? 'bg-green-500' : 'bg-gray-500'}`} />
      )}
      {isImposter && (
        <span className="absolute -top-1 -left-1 bg-red-600 text-white text-[9px] font-bold px-1 rounded-full leading-none">
          I
        </span>
      )}
    </div>
  );
}
