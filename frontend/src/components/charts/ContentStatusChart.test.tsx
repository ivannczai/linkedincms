import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ContentStatusChart from './ContentStatusChart';
import { ContentStatus } from '../../services/contents';

// Mock the recharts library
vi.mock('recharts', async () => {
    const actual = await vi.importActual('recharts') as object; // Cast actual to object
    return {
        ...actual, // Spread as object
        ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
            <div data-testid="responsive-container">{children}</div>
        ),
        PieChart: ({ children }: { children: React.ReactNode }) => (
            <div data-testid="pie-chart">{children}</div>
        ),
        Pie: ({ data }: { data: any[] }) => (
            <div data-testid="pie" data-props={JSON.stringify(data)}>Pie</div>
        ),
        Cell: ({ fill }: { fill: string }) => <div data-testid="cell" data-fill={fill}></div>,
        Tooltip: () => <div data-testid="tooltip">Tooltip</div>,
        Legend: () => <div data-testid="legend">Legend</div>,
    };
});

describe('ContentStatusChart', () => {
    it('renders "No data" message when all counts are zero', () => {
        const zeroCounts = { pending: 0, revision: 0, approved: 0, scheduled: 0, published: 0 };
        render(<ContentStatusChart counts={zeroCounts} />);
        expect(screen.getByText(/No content data available for chart/i)).toBeInTheDocument();
        expect(screen.queryByTestId('responsive-container')).not.toBeInTheDocument();
    });

    it('renders the chart components when there is data', () => {
        const someCounts = { pending: 1, revision: 2, approved: 3, scheduled: 2, published: 4 };
        render(<ContentStatusChart counts={someCounts} />);
        expect(screen.queryByText(/No content data available for chart/i)).not.toBeInTheDocument();
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
        expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
        expect(screen.getByTestId('pie')).toBeInTheDocument();
        expect(screen.getByTestId('tooltip')).toBeInTheDocument();
        expect(screen.getByTestId('legend')).toBeInTheDocument();
    });

    it('passes correctly formatted data to the Pie component', () => {
        const someCounts = { pending: 1, revision: 2, approved: 3, scheduled: 2, published: 4 };
        render(<ContentStatusChart counts={someCounts} />);
        const pieElement = screen.getByTestId('pie');
        const pieData = JSON.parse(pieElement.getAttribute('data-props') || '[]');

        expect(pieData).toHaveLength(4);
        expect(pieData).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ name: 'Pending Approval', value: 1, status: ContentStatus.PENDING_APPROVAL }),
                expect.objectContaining({ name: 'Revision Requested', value: 2, status: ContentStatus.REVISION_REQUESTED }),
                expect.objectContaining({ name: 'Approved', value: 3, status: ContentStatus.APPROVED }),
                expect.objectContaining({ name: 'Published', value: 4, status: ContentStatus.PUBLISHED }),
            ])
        );
    });

    it('filters out statuses with zero count from Pie data', () => {
        const partialCounts = { pending: 0, revision: 2, approved: 3, scheduled: 1, published: 0 };
        render(<ContentStatusChart counts={partialCounts} />);
        const pieElement = screen.getByTestId('pie');
        const pieData = JSON.parse(pieElement.getAttribute('data-props') || '[]');

        expect(pieData).toHaveLength(2);
        expect(pieData).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ name: 'Revision Requested', value: 2 }),
                expect.objectContaining({ name: 'Approved', value: 3 }),
            ])
        );
        expect(pieData).not.toEqual(
            expect.arrayContaining([
                expect.objectContaining({ name: 'Pending Approval' }),
                expect.objectContaining({ name: 'Published' }),
            ])
        );
    });

    // Note: Testing exact colors rendered by Cells within the mock is complex.
    // We trust that recharts uses the 'fill' prop correctly.
});
