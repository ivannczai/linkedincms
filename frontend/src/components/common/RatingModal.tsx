import React, { useState } from 'react';
import CustomStarRating from './CustomStarRating'; // Import the new custom component

interface RatingModalProps {
  isOpen: boolean;
  onClose: (rated: boolean) => void; // Indicate if rating was submitted
  onSubmitRating: (rating: number) => Promise<void>; // Function to call the rating API
  contentTitle: string;
}

const RatingModal: React.FC<RatingModalProps> = ({ 
  isOpen, 
  onClose, 
  onSubmitRating,
  contentTitle 
}) => {
  const [rating, setRating] = useState<number>(0); // Initial rating state
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRatingChange = (newRating: number) => {
    setRating(newRating);
    setError(null); // Clear error when rating changes
  };

  const handleSubmit = async () => {
    if (rating === 0) {
      setError("Please select a rating (at least 0.5 stars).");
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmitRating(rating);
      onClose(true); // Close modal and indicate rating was submitted
    } catch (err: any) {
      console.error("Failed to submit rating:", err);
      setError(err.message || "Failed to submit rating. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseWithoutRating = () => {
     onClose(false); // Close modal, indicate no rating was submitted
  };

  if (!isOpen) {
    return null;
  }

  return (
    // Modal backdrop
    <div 
      className="fixed inset-0 bg-gray-800 bg-opacity-75 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4 transition-opacity duration-300 ease-in-out"
      onClick={handleCloseWithoutRating} // Close on backdrop click
    >
      {/* Modal Panel - Use card style implicitly via bg-white, shadow, rounded */}
      <div 
        className={`relative mx-auto w-full max-w-md bg-white rounded-lg shadow-xl transition-transform duration-300 ease-in-out ${isOpen ? 'scale-100' : 'scale-95'}`}
        onClick={(e) => e.stopPropagation()} 
      >
        {/* Modal Header */}
        <div className="flex justify-between items-center border-b border-gray-200 p-4"> 
          <h3 className="text-lg font-semibold text-brand-foreground">Rate Content</h3>
          <button
            onClick={handleCloseWithoutRating}
            className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center" 
            aria-label="Close modal"
          >
             <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
          </button>
        </div>
        
        {/* Modal Body - Increased padding, adjusted text */}
        <div className="p-8 space-y-5 text-center"> 
           <p className="text-lg text-gray-700">How would you rate this content?</p> 
           <p className="text-xl font-semibold text-brand-foreground truncate" title={contentTitle}>{contentTitle}</p> 
           
           <div className="flex justify-center py-2"> 
             <CustomStarRating 
               rating={rating} // Pass state to 'rating' prop
               onRatingChange={handleRatingChange} 
               size={40} 
             />
           </div>

           {error && (
             <p className="text-sm text-red-600">{error}</p> 
           )}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end items-center border-t border-gray-200 p-4 space-x-3"> 
          <button
            onClick={handleCloseWithoutRating}
            className="btn btn-secondary" 
            disabled={isSubmitting}
          >
            Cancel / Rate Later
          </button>
          <button
            onClick={handleSubmit}
            className="btn btn-primary"
            disabled={isSubmitting || rating === 0}
          >
            {isSubmitting ? 'Submitting...' : 'Confirm Rating'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RatingModal;
