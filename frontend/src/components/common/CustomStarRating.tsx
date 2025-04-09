import React, { useState } from 'react';
import { Star } from 'lucide-react';
import { cn } from '../../utils/cn'; // Import the new utility

interface CustomStarRatingProps {
  rating: number | null | undefined; // Current rating (0-5)
  onRatingChange?: (newRating: number) => void; // Callback for when rating changes
  readOnly?: boolean;
  size?: number; // Size of the stars in pixels
  allowHalf?: boolean;
  className?: string;
  starClassName?: string; // Allow custom styling for individual stars
}

const CustomStarRating: React.FC<CustomStarRatingProps> = ({
  rating,
  onRatingChange,
  readOnly = false,
  size = 24,
  allowHalf = true,
  className = '',
  starClassName = 'text-yellow-400', // Default star color
}) => {
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const currentRating = rating ?? 0;
  const displayRating = hoverRating ?? currentRating; // Show hover state if active

  const handleMouseLeave = () => {
    if (!readOnly) {
      setHoverRating(null);
    }
  };

  const handleClick = (index: number, isHalf: boolean) => {
    if (!readOnly && onRatingChange) {
      const newRating = index + (isHalf ? 0.5 : 1);
      onRatingChange(newRating);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>, index: number) => {
    if (!readOnly && allowHalf) {
      const starElement = e.currentTarget;
      const rect = starElement.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const isHalf = mouseX < rect.width / 2;
      setHoverRating(index + (isHalf ? 0.5 : 1));
    } else if (!readOnly) {
       setHoverRating(index + 1); // Hover full star if half not allowed
    }
  };
   
  const handleMouseEnter = (index: number) => {
     if (!readOnly && !allowHalf) {
        setHoverRating(index + 1);
     }
     // Half star hover is handled by mouseMove
  }

  return (
    <div 
      className={cn('flex', className)} 
      onMouseLeave={handleMouseLeave}
      aria-label={`Rating: ${currentRating} out of 5 stars`}
      role={readOnly ? 'img' : 'slider'}
      aria-valuemin={0}
      aria-valuemax={5}
      aria-valuenow={currentRating}
      aria-readonly={readOnly}
    >
      {[...Array(5)].map((_, index) => {
        const starValue = index + 1;
        const isFilled = displayRating >= starValue;
        const isHalfFilled = allowHalf && displayRating >= starValue - 0.5 && displayRating < starValue;

        return (
          <div
            key={index}
            className={cn('relative', !readOnly ? 'cursor-pointer' : '')}
            onClick={(e) => {
               // Determine if click was on first or second half for half-star logic
               const starElement = e.currentTarget;
               const rect = starElement.getBoundingClientRect();
               const clickX = e.clientX - rect.left;
               const clickedHalf = allowHalf && clickX < rect.width / 2;
               handleClick(index, clickedHalf);
            }}
            onMouseMove={(e) => handleMouseMove(e, index)}
            onMouseEnter={() => handleMouseEnter(index)} // Handle full star hover when half not allowed
            style={{ width: size, height: size }}
          >
            {/* Background Star (Empty) */}
            <Star
              size={size}
              className={cn('absolute inset-0 text-gray-300', starClassName)}
              aria-hidden="true"
            />
            {/* Filled Star Portion */}
            {(isFilled || isHalfFilled) && (
              <Star
                size={size}
                className={cn('absolute inset-0 fill-current', starClassName)}
                style={{ 
                   clipPath: isHalfFilled ? 'inset(0 50% 0 0)' : 'none' 
                }}
                aria-hidden="true"
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default CustomStarRating;
