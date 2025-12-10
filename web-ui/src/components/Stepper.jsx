import React from 'react';

const steps = [
  { id: 1, name: 'Input', key: 'input' },
  { id: 2, name: 'Build', key: 'build' },
  { id: 3, name: 'Edit', key: 'edit' },
  { id: 4, name: 'Execute', key: 'execute' },
  { id: 5, name: 'Review', key: 'review' },
];

export const Stepper = ({ currentStep }) => {
  const currentStepNumber = steps.findIndex(s => s.key === currentStep) + 1;
  
  return (
    <div className="w-full bg-white border-b border-gray-100 py-6">
      <div className="max-w-5xl mx-auto px-8">
        {/* Step Labels - Rounded Boxes */}
        <div className="flex justify-between items-center gap-3">
          {steps.map((step) => {
            const isComplete = step.id < currentStepNumber;
            const isCurrent = step.id === currentStepNumber;
            
            return (
              <div 
                key={step.id}
                className={`
                  px-6 py-3 rounded-full text-sm font-semibold whitespace-nowrap
                  transition-all duration-500 shadow-sm
                  ${isComplete 
                    ? 'bg-gray-400 text-white' 
                    : isCurrent
                      ? 'bg-primary-600 text-white ring-4 ring-primary-100 scale-105 shadow-md'
                      : 'bg-gray-100 text-gray-400 border border-gray-200'
                  }
                  flex-1 text-center
                `}
              >
                {step.name}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
