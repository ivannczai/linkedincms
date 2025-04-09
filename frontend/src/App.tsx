import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import React, { useState } from 'react'; // Keep single React import
import { useAuth } from './context/AuthContext';
import Sidebar from './components/layout/Sidebar';
// NavLink removed as it's unused here
import { Menu } from 'lucide-react';

// Import dashboard pages
import AdminDashboardPage from './pages/admin/DashboardPage';
import ClientDashboard from './pages/client/ClientDashboard';
import SettingsPage from './pages/SettingsPage'; // Import SettingsPage
import LinkedInSchedulerPage from './pages/LinkedInSchedulerPage'; // Import LinkedInSchedulerPage

// Root redirect component
const RootRedirect = () => {
  const { user } = useAuth();

  if (user?.role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />;
  } else if (user?.role === 'client') {
    return <Navigate to="/client/dashboard" replace />;
  } else {
    return <Navigate to="/login" replace />;
  }
};

// Layout component
const Layout = ({ children }: { children: React.ReactNode }) => {
  const { user, logout } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Removed unused NavLink class variables

  return (
    <div className="min-h-screen flex bg-gray-100 relative">
      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />

      <div className="flex-1 flex flex-col md:ml-64">
        <header className="bg-white shadow-sm sticky top-0 z-20 border-b border-gray-200">
          <div className="max-w-full mx-auto py-2.5 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
             <button
               onClick={() => setIsSidebarOpen(true)}
               className="md:hidden p-1 text-gray-500 hover:text-gray-700"
               aria-label="Open sidebar"
             >
                <Menu className="h-6 w-6" />
             </button>
             <div className="hidden md:block flex-1"></div>
            {user && (
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-500 hidden sm:inline">
                {user.email} ({user.role})
              </span>
              <button
                onClick={logout}
                className="btn btn-ghost px-3 py-1.5 text-sm"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="flex-grow p-6">
        {children}
      </main>
    </div>
  </div>
  );
};

// Import admin pages
import ClientsPage from './pages/admin/ClientsPage';
import CreateClientPage from './pages/admin/CreateClientPage';
import EditClientPage from './pages/admin/EditClientPage';
import ClientDetailPage from './pages/admin/ClientDetailPage';
import CreateContentPage from './pages/admin/CreateContentPage';
import ContentViewPage from './pages/admin/ContentViewPage';
import EditContentPage from './pages/admin/EditContentPage';
import AllContentPage from './pages/admin/AllContentPage';
import CreateGlobalContentPage from './pages/admin/CreateGlobalContentPage';

// Import client pages
import ClientContentViewPage from './pages/client/ClientContentViewPage';
import ClientContentLibraryPage from './pages/client/ClientContentLibraryPage';

// Root component with routes
function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes (accessible by admin or client) */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<RootRedirect />} />
            {/* Add Settings route here, accessible by both roles */}
            <Route path="/dashboard/settings" element={<Layout><SettingsPage /></Layout>} />
            {/* Add LinkedIn Scheduler route here */}
            <Route path="/dashboard/linkedin/schedule" element={<Layout><LinkedInSchedulerPage /></Layout>} />
          </Route>

          {/* Admin routes */}
          <Route element={<ProtectedRoute requiredRole="admin" />}>
            <Route path="/admin/dashboard" element={<Layout><AdminDashboardPage /></Layout>} />
            <Route path="/admin/content" element={<Layout><AllContentPage /></Layout>} />
            <Route path="/admin/content/new" element={<Layout><CreateGlobalContentPage /></Layout>} />
            <Route path="/admin/clients" element={<Layout><ClientsPage /></Layout>} />
            <Route path="/admin/clients/new" element={<Layout><CreateClientPage /></Layout>} />
            <Route path="/admin/clients/:clientId" element={<Layout><ClientDetailPage /></Layout>} />
            <Route path="/admin/clients/:id/edit" element={<Layout><EditClientPage /></Layout>} />
            <Route path="/admin/clients/:clientId/contents/new" element={<Layout><CreateContentPage /></Layout>} />
            <Route path="/admin/clients/:clientId/contents/:contentId" element={<Layout><ContentViewPage /></Layout>} />
            <Route path="/admin/clients/:clientId/contents/:contentId/edit" element={<Layout><EditContentPage /></Layout>} />
            {/* Consider if /dashboard/settings and /dashboard/linkedin/schedule should also be explicitly listed here if needed */}
          </Route>

          {/* Client routes */}
          <Route element={<ProtectedRoute requiredRole="client" />}>
            <Route path="/client/dashboard" element={<Layout><ClientDashboard /></Layout>} />
            <Route path="/client/library" element={<Layout><ClientContentLibraryPage /></Layout>} />
            <Route path="/client/contents/:id" element={<Layout><ClientContentViewPage /></Layout>} />
             {/* Consider if /dashboard/settings and /dashboard/linkedin/schedule should also be explicitly listed here if needed */}
          </Route>

          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
