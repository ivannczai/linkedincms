import React from 'react';
import { Strategy } from '../../services/strategies';
import StrategyView from './StrategyView'; // Reuse the existing view component

interface StrategyViewModalProps {
  strategy: Strategy | null;
  isOpen: boolean;
  onClose: () => void;
}

const StrategyViewModal: React.FC<StrategyViewModalProps> = ({ strategy, isOpen, onClose }) => {
  if (!isOpen || !strategy) {
    return null;
  }

  return (
    // Modal backdrop
    <div 
      className={`fixed inset-0 bg-gray-800 bg-opacity-75 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4 transition-opacity duration-300 ease-in-out ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      onClick={onClose} // Close on backdrop click
    >
      {/* Modal Panel */}
      <div 
        className={`relative mx-auto border border-gray-200 w-full max-w-3xl shadow-xl rounded-lg bg-white transition-transform duration-300 ease-in-out ${isOpen ? 'scale-100' : 'scale-95'}`}
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
      >
        {/* Modal Header */}
        <div className="flex justify-between items-center border-b border-gray-200 p-5">
          <h3 className="text-lg font-semibold text-brand-foreground">Strategy Details: {strategy.title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center"
            aria-label="Close modal"
          >
             <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
          </button>
        </div>
        {/* Modal Body */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {/* Use StrategyView, ensure it doesn't have conflicting background/padding */}
          <StrategyView strategy={strategy} isAdmin={false} /> 
        </div>
        {/* Modal Footer */}
        <div className="flex justify-end items-center border-t border-gray-200 p-4 space-x-2">
          <button
            onClick={onClose}
            className="btn btn-secondary" // Use new button style
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategyViewModal;
