import React from 'react';
import { Rating } from 'react-simple-star-rating';
// Remove unused Star import from lucide-react

interface StarRatingInputProps {
  ratingValue: number | null | undefined; // Current rating (0-5)
  onRatingChange?: (newRating: number) => void; // Callback for when rating changes
  readOnly?: boolean;
  size?: number; // Size of the stars
  allowHalfIcon?: boolean;
  className?: string;
}

const StarRatingInput: React.FC<StarRatingInputProps> = ({
  ratingValue,
  onRatingChange,
  readOnly = false,
  size = 24, // Default size
  allowHalfIcon = true,
  className = '',
}) => {
  
  // Convert rating (0-5) to the library's expected scale (0-100) if needed, 
  // Use the ratingValue prop directly for initialValue.
  // The component becomes controlled by the parent state.
  // Use the ratingValue prop for initialValue.
  const initialRating = ratingValue !== null && ratingValue !== undefined ? ratingValue : 0;

  const handleRating = (rate: number) => {
    // Pass the 0-5 value directly to the parent
    if (onRatingChange) {
      onRatingChange(rate);
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      <Rating
        onClick={handleRating}
        initialValue={initialRating} // Use initialValue based on the prop
        /* Removed ratingValue prop as it causes TS errors */
        size={size}
        allowFraction={allowHalfIcon} 
        readonly={readOnly}
        transition
        fillColor="currentColor" // Use text color for fill
        emptyColor="currentColor" // Use text color for empty
        className={`text-yellow-400 ${readOnly ? '' : 'cursor-pointer'}`} // Base color, pointer if editable
        // Custom icons using Lucide (optional, requires more setup if needed)
        // fillIcon={<Star size={size} className="text-yellow-400 fill-current" />} 
        // emptyIcon={<Star size={size} className="text-gray-300" />} 
      />
      {/* Optionally display the numeric value */}
      {/* {!readOnly && ratingValue !== null && ratingValue !== undefined && (
         <span className="ml-2 text-sm font-medium text-gray-600">({ratingValue}/5)</span>
      )} */}
    </div>
  );
};

export default StarRatingInput;
