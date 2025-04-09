import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, FileText, Library, Settings, Link2, X } from 'lucide-react'; // Added Settings, Link2 icons
import { useAuth } from '../../context/AuthContext';

// Define props for the sidebar state
interface SidebarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen }) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const isClient = user?.role === 'client';

  // Common link classes
  const linkClasses = "flex items-center px-3 py-2.5 rounded-md text-sm font-medium text-gray-300 hover:bg-secondary-700 hover:text-white transition-colors duration-150";
  const activeLinkClasses = "bg-secondary-800 text-white font-semibold";

  // Base classes + conditional transform for mobile responsiveness
  const sidebarBaseClasses = "w-64 h-screen bg-secondary-900 text-secondary-100 flex flex-col fixed shadow-lg z-30 transition-transform duration-300 ease-in-out";
  const sidebarMobileClosed = "-translate-x-full";
  const sidebarMobileOpen = "translate-x-0";
  const sidebarDesktop = "md:translate-x-0"; // Always visible on md+

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        ></div>
      )}

      {/* Sidebar */}
      <div className={`${sidebarBaseClasses} ${isOpen ? sidebarMobileOpen : sidebarMobileClosed} ${sidebarDesktop}`}>
        {/* Header */}
        <div className="flex items-center justify-between h-16 border-b border-secondary-700 px-4">
           <span className="text-xl font-bold text-white">
             {isAdmin ? 'Admin Panel' : 'Content Hub'}
           </span>
           {/* Close button for mobile */}
           <button
             onClick={() => setIsOpen(false)}
             className="md:hidden p-1 text-gray-400 hover:text-white"
             aria-label="Close sidebar"
           >
              <X className="h-6 w-6" />
           </button>
        </div>
        {/* Navigation */}
        <nav className="flex-grow p-4 space-y-1 overflow-y-auto"> {/* Added overflow-y-auto */}
          {/* Admin Links */}
          {isAdmin && (
            <>
              <NavLink
                to="/admin/dashboard"
                className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                onClick={() => setIsOpen(false)} // Close sidebar on mobile nav click
              >
                <LayoutDashboard className="mr-3 h-5 w-5" />
                Dashboard
              </NavLink>
              <NavLink
                to="/admin/clients"
                className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                 onClick={() => setIsOpen(false)}
              >
                 <Users className="mr-3 h-5 w-5" />
                Clients
              </NavLink>
              <NavLink
                to="/admin/content"
                className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                 onClick={() => setIsOpen(false)}
              >
                 <FileText className="mr-3 h-5 w-5" />
                Content
              </NavLink>
              {/* Add LinkedIn Scheduler Link for Admin */}
              <NavLink
                to="/dashboard/linkedin/schedule" // Use the common route
                className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                onClick={() => setIsOpen(false)}
              >
                <Link2 className="mr-3 h-5 w-5" /> {/* Using Link2 icon */}
                LinkedIn Scheduler
              </NavLink>
            </>
          )}

          {/* Client Links */}
          {isClient && (
             <>
               <NavLink
                 to="/client/dashboard"
                 className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                  onClick={() => setIsOpen(false)}
               >
                 <LayoutDashboard className="mr-3 h-5 w-5" />
                 Dashboard
               </NavLink>
               <NavLink
                 to="/client/library"
                 className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                  onClick={() => setIsOpen(false)}
               >
                  <Library className="mr-3 h-5 w-5" />
                 Content Library
               </NavLink>
               {/* Add LinkedIn Scheduler Link for Client */}
               <NavLink
                 to="/dashboard/linkedin/schedule" // Use the common route
                 className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
                 onClick={() => setIsOpen(false)}
               >
                 <Link2 className="mr-3 h-5 w-5" /> {/* Using Link2 icon */}
                 LinkedIn Scheduler
               </NavLink>
             </>
          )}

          {/* Common Links (Settings) */}
          {(isAdmin || isClient) && (
            <NavLink
              to="/dashboard/settings"
              className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}
              onClick={() => setIsOpen(false)}
            >
              <Settings className="mr-3 h-5 w-5" />
              Settings
            </NavLink>
          )}
        </nav>
        <div className="p-4 border-t border-gray-700 text-xs text-gray-400">
          {/* Footer or version info */}
        </div>
      </div>
    </>
  );
};

export default Sidebar;
