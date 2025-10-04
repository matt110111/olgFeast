import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import MenuList from './components/Menu/MenuList';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; requireAuth?: boolean; requireStaff?: boolean }> = ({ 
  children, 
  requireAuth = true, 
  requireStaff = false 
}) => {
  const { isAuthenticated, isStaff, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireStaff && !isStaff) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

// Home Page Component
const HomePage: React.FC = () => {
  return (
    <Layout>
      <MenuList />
    </Layout>
  );
};

// Cart Page Component (placeholder)
const CartPage: React.FC = () => {
  return (
    <Layout>
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Shopping Cart</h1>
        <p className="mt-2 text-gray-600">Cart functionality coming soon...</p>
      </div>
    </Layout>
  );
};

// Orders Page Component (placeholder)
const OrdersPage: React.FC = () => {
  return (
    <Layout>
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">My Orders</h1>
        <p className="mt-2 text-gray-600">Order history coming soon...</p>
      </div>
    </Layout>
  );
};

// Kitchen Display Page Component (placeholder)
const KitchenPage: React.FC = () => {
  return (
    <Layout>
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Kitchen Display</h1>
        <p className="mt-2 text-gray-600">Real-time kitchen display coming soon...</p>
      </div>
    </Layout>
  );
};

// Admin Dashboard Page Component (placeholder)
const AdminPage: React.FC = () => {
  return (
    <Layout>
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">Analytics and management coming soon...</p>
      </div>
    </Layout>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          
          {/* Protected Routes */}
          <Route 
            path="/cart" 
            element={
              <ProtectedRoute>
                <CartPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/orders" 
            element={
              <ProtectedRoute>
                <OrdersPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Staff Only Routes */}
          <Route 
            path="/kitchen" 
            element={
              <ProtectedRoute requireStaff>
                <KitchenPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute requireStaff>
                <AdminPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
