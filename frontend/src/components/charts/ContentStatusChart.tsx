import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ContentStatus } from '../../services/contents'; // Assuming ContentStatus enum is here

interface ContentStatusChartProps {
  counts: {
    pending: number;
    revision: number;
    approved: number;
    scheduled: number;
    published: number;
    // Add draft if needed/available
  };
}

// Define colors for each status (Tailwind colors can be used if configured)
const COLORS = {
  [ContentStatus.PENDING_APPROVAL]: '#FBBF24', // amber-400
  [ContentStatus.REVISION_REQUESTED]: '#F87171', // red-400
  [ContentStatus.APPROVED]: '#34D399', // emerald-400
  [ContentStatus.SCHEDULED]: '#A78BFA', // purple-400
  [ContentStatus.PUBLISHED]: '#60A5FA', // blue-400
  [ContentStatus.DRAFT]: '#9CA3AF', // gray-400 
};

const ContentStatusChart: React.FC<ContentStatusChartProps> = ({ counts }) => {
  const data = [
    { name: 'Pending Approval', value: counts.pending, status: ContentStatus.PENDING_APPROVAL },
    { name: 'Revision Requested', value: counts.revision, status: ContentStatus.REVISION_REQUESTED },
    { name: 'Approved', value: counts.approved, status: ContentStatus.APPROVED },
    { name: 'Scheduled', value: counts.scheduled, status: ContentStatus.SCHEDULED },
    { name: 'Published', value: counts.published, status: ContentStatus.PUBLISHED },
    // Add Draft if you track it separately
  ].filter(entry => entry.value > 0); // Only show statuses with count > 0

  if (data.length === 0) {
    return <p className="text-center text-gray-500 italic">No content data available for chart.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
          nameKey="name"
          // label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} // Optional: label on slices
        >
          {data.map((entry) => (
            <Cell key={`cell-${entry.status}`} fill={COLORS[entry.status] || '#8884d8'} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => [`${value} piece(s)`, undefined]} />
        <Legend verticalAlign="bottom" height={36}/>
      </PieChart>
    </ResponsiveContainer>
  );
};

export default ContentStatusChart;
