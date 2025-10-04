import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import MenuList from './components/Menu/MenuList';
import CartList from './components/Cart/CartList';
import OrderList from './components/Orders/OrderList';
import KitchenDisplay from './components/Kitchen/KitchenDisplay';
import AdminDashboard from './components/Admin/AdminDashboard';
import CheckoutForm from './components/Checkout/CheckoutForm';

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

// Cart Page Component
const CartPage: React.FC = () => {
  return (
    <Layout>
      <CartList />
    </Layout>
  );
};

// Orders Page Component
const OrdersPage: React.FC = () => {
  return (
    <Layout>
      <OrderList />
    </Layout>
  );
};

// Kitchen Display Page Component
const KitchenPage: React.FC = () => {
  return (
    <Layout>
      <KitchenDisplay />
    </Layout>
  );
};

// Admin Dashboard Page Component
const AdminPage: React.FC = () => {
  return (
    <Layout>
      <AdminDashboard />
    </Layout>
  );
};

// Checkout Page Component
const CheckoutPage: React.FC = () => {
  return (
    <Layout>
      <CheckoutForm />
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
                 <Route
                   path="/checkout"
                   element={
                     <ProtectedRoute>
                       <CheckoutPage />
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
