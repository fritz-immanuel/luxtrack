import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:8000';
const API = `${BACKEND_URL.replace(/\/$/, '')}/api`;

// Create Auth Context
const AuthContext = createContext();

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Verify token and get user info
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/users/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Modal Component
const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

// Image Upload Component
const ImageUpload = ({ images, onChange }) => {
  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    const maxFiles = 10;
    
    if (files.length > maxFiles) {
      alert(`Maximum ${maxFiles} images allowed`);
      return;
    }

    files.forEach(file => {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        alert('Each image must be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target.result;
        onChange([...images, base64]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    onChange(newImages);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Images</label>
      
      {/* Upload Area */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center mb-4">
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleImageUpload}
          className="hidden"
          id="image-upload"
        />
        <label
          htmlFor="image-upload"
          className="cursor-pointer text-blue-600 hover:text-blue-800"
        >
          📷 Click to upload images (max 10, 5MB each)
        </label>
      </div>

      {/* Image Preview Grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {images.map((image, index) => (
            <div key={index} className="relative">
              <img
                src={image}
                alt={`Preview ${index + 1}`}
                className="w-full h-32 object-cover rounded border"
              />
              <button
                type="button"
                onClick={() => removeImage(index)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Login Component
const Login = () => {
  const [email, setEmail] = useState('admin@luxtrack.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await login(email, password);
    if (!result.success) {
      setError(result.error);
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">LuxTrack</h2>
          <p className="mt-2 text-sm text-gray-600">Luxury Goods Inventory System</p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="text-sm text-gray-500">
              <p>Default credentials:</p>
              <p>Email: admin@luxtrack.com</p>
              <p>Password: admin123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'products', name: 'Products', icon: '📦' },
    { id: 'customers', name: 'Customers', icon: '👥' },
    { id: 'sources', name: 'Sources', icon: '🏪' },
    { id: 'transactions', name: 'Transactions', icon: '💰' },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">LuxTrack</h1>
            </div>
            <div className="hidden md:ml-6 md:flex md:space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-gray-900 bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-3 border-b-2 font-medium text-sm rounded-t-lg transition-colors duration-200`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              {user?.full_name} ({user?.role})
            </span>
            <button
              onClick={logout}
              className="text-gray-500 hover:text-gray-700 text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
      <TabContent activeTab={activeTab} />
    </nav>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6">Loading dashboard...</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold">📦</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Products</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.total_products || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-semibold">✅</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Available</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.available_products || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 font-semibold">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Customers</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.total_customers || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <span className="text-orange-600 font-semibold">🏪</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Sources</p>
              <p className="text-2xl font-semibold text-gray-900">{stats?.total_sources || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-semibold">💰</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Revenue</p>
              <p className="text-2xl font-semibold text-gray-900">${stats?.total_revenue?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
        </div>
        <div className="px-6 py-4">
          {stats?.recent_transactions?.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_transactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0 cursor-pointer hover:bg-gray-50 rounded px-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)} - 
                      ${transaction.total_amount.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(transaction.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    transaction.status === 'completed' ? 'bg-green-100 text-green-800' :
                    transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {transaction.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No recent transactions</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Products Component
const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = async (product) => {
    try {
      const response = await axios.get(`${API}/products/${product.id}/details`);
      setSelectedProduct(response.data);
    } catch (error) {
      console.error('Failed to fetch product details:', error);
    }
  };

  if (loading) {
    return <div className="p-6">Loading products...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Products</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          {showForm ? 'Cancel' : 'Add Product'}
        </button>
      </div>

      {showForm && <ProductForm onSuccess={() => { fetchProducts(); setShowForm(false); }} onCancel={() => setShowForm(false)} />}

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Brand</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Condition</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {products.map((product) => (
              <tr 
                key={product.id} 
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => handleProductClick(product)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.code}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.brand}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.condition}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    product.status === 'available' ? 'bg-green-100 text-green-800' :
                    product.status === 'sold' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {product.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ${product.selling_price?.toFixed(2) || product.purchase_price.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {products.length === 0 && (
          <div className="text-center py-8 text-gray-500">No products found</div>
        )}
      </div>

      {/* Product Detail Modal */}
      <Modal
        isOpen={!!selectedProduct}
        onClose={() => setSelectedProduct(null)}
        title="Product Details"
      >
        {selectedProduct && <ProductDetailView product={selectedProduct} />}
      </Modal>
    </div>
  );
};

// Product Detail View Component
const ProductDetailView = ({ product }) => {
  return (
    <div className="space-y-6">
      {/* Product Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Product Information</h3>
          <div className="space-y-2 text-sm">
            <p><span className="font-medium">Code:</span> {product.product.code}</p>
            <p><span className="font-medium">Name:</span> {product.product.name}</p>
            <p><span className="font-medium">Brand:</span> {product.product.brand}</p>
            <p><span className="font-medium">Category:</span> {product.product.category}</p>
            <p><span className="font-medium">Condition:</span> {product.product.condition}</p>
            <p><span className="font-medium">Status:</span> {product.product.status}</p>
            <p><span className="font-medium">Purchase Price:</span> ${product.product.purchase_price}</p>
            {product.product.selling_price && (
              <p><span className="font-medium">Selling Price:</span> ${product.product.selling_price}</p>
            )}
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Source Information</h3>
          {product.source ? (
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Source:</span> {product.source.name}</p>
              <p><span className="font-medium">Type:</span> {product.source.source_type}</p>
              {product.source.contact_person && (
                <p><span className="font-medium">Contact:</span> {product.source.contact_person}</p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No source information</p>
          )}
        </div>
      </div>

      {/* Images */}
      {product.product.images && product.product.images.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Images</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {product.product.images.map((image, index) => (
              <img
                key={index}
                src={image}
                alt={`Product ${index + 1}`}
                className="w-full h-32 object-cover rounded border"
              />
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      {product.product.description && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
          <p className="text-sm text-gray-600">{product.product.description}</p>
        </div>
      )}

      {/* Transactions */}
      {product.transactions && product.transactions.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Transaction History</h3>
          <div className="space-y-2">
            {product.transactions.map((tx) => (
              <div key={tx.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{tx.transaction_type} - ${tx.total_amount}</span>
                  <span className={`px-2 py-1 text-xs rounded ${
                    tx.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {tx.status}
                  </span>
                </div>
                <p className="text-gray-500">{new Date(tx.created_at).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Product Form Component
const ProductForm = ({ onSuccess, onCancel }) => {
  const [sources, setSources] = useState([]);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    brand: '',
    category: '',
    condition: 'excellent',
    purchase_price: '',
    selling_price: '',
    description: '',
    source_id: ''
  });
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const response = await axios.get(`${API}/sources`);
      setSources(response.data);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const submitData = {
        ...formData,
        purchase_price: parseFloat(formData.purchase_price),
        selling_price: formData.selling_price ? parseFloat(formData.selling_price) : null,
        source_id: formData.source_id || null,
        images: images
      };

      await axios.post(`${API}/products`, submitData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Product</h3>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
            <input
              type="text"
              name="code"
              value={formData.code}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
            <input
              type="text"
              name="brand"
              value={formData.brand}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <input
              type="text"
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
            <select
              name="condition"
              value={formData.condition}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="excellent">Excellent</option>
              <option value="very_good">Very Good</option>
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
            <select
              name="source_id"
              value={formData.source_id}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a source (optional)</option>
              {sources.map(source => (
                <option key={source.id} value={source.id}>
                  {source.name} ({source.source_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
            <input
              type="number"
              step="0.01"
              name="purchase_price"
              value={formData.purchase_price}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price (Optional)</label>
            <input
              type="number"
              step="0.01"
              name="selling_price"
              value={formData.selling_price}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <ImageUpload images={images} onChange={setImages} />

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Product'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Customers Component (updated with clickable rows)
const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerClick = async (customer) => {
    try {
      const response = await axios.get(`${API}/customers/${customer.id}/details`);
      setSelectedCustomer(response.data);
    } catch (error) {
      console.error('Failed to fetch customer details:', error);
    }
  };

  if (loading) {
    return <div className="p-6">Loading customers...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Customers</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          {showForm ? 'Cancel' : 'Add Customer'}
        </button>
      </div>

      {showForm && <CustomerForm onSuccess={() => { fetchCustomers(); setShowForm(false); }} onCancel={() => setShowForm(false)} />}

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {customers.map((customer) => (
              <tr 
                key={customer.id} 
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => handleCustomerClick(customer)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{customer.full_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.email || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.phone || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(customer.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {customers.length === 0 && (
          <div className="text-center py-8 text-gray-500">No customers found</div>
        )}
      </div>

      {/* Customer Detail Modal */}
      <Modal
        isOpen={!!selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
        title="Customer Details"
      >
        {selectedCustomer && <CustomerDetailView customer={selectedCustomer} />}
      </Modal>
    </div>
  );
};

// Customer Detail View Component
const CustomerDetailView = ({ customer }) => {
  return (
    <div className="space-y-6">
      {/* Customer Info */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Contact Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p><span className="font-medium">Name:</span> {customer.customer.full_name}</p>
            <p><span className="font-medium">Email:</span> {customer.customer.email || 'N/A'}</p>
            <p><span className="font-medium">Phone:</span> {customer.customer.phone || 'N/A'}</p>
            <p><span className="font-medium">Address:</span> {customer.customer.address || 'N/A'}</p>
          </div>
          <div>
            <p><span className="font-medium">Total Purchases:</span> ${customer.total_purchases?.toFixed(2) || '0.00'}</p>
            <p><span className="font-medium">Total Sales:</span> ${customer.total_sales?.toFixed(2) || '0.00'}</p>
            <p><span className="font-medium">Transaction Count:</span> {customer.transaction_count || 0}</p>
          </div>
        </div>
      </div>

      {/* Notes */}
      {customer.customer.notes && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Notes</h3>
          <p className="text-sm text-gray-600">{customer.customer.notes}</p>
        </div>
      )}

      {/* Transaction History */}
      {customer.transactions && customer.transactions.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Transaction History</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {customer.transactions.map((tx) => (
              <div key={tx.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="font-medium">
                    {tx.transaction_type.charAt(0).toUpperCase() + tx.transaction_type.slice(1)} - ${tx.total_amount}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded ${
                    tx.status === 'completed' ? 'bg-green-100 text-green-800' : 
                    tx.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {tx.status}
                  </span>
                </div>
                <p className="text-gray-500">{new Date(tx.created_at).toLocaleDateString()}</p>
                {tx.notes && <p className="text-gray-600 text-xs mt-1">{tx.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Customer Form Component (unchanged)
const CustomerForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    address: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const submitData = {
        ...formData,
        email: formData.email || null,
        phone: formData.phone || null,
        address: formData.address || null,
        notes: formData.notes || null
      };

      await axios.post(`${API}/customers`, submitData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Customer</h3>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
          <input
            type="text"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Customer'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Sources Component
const Sources = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const response = await axios.get(`${API}/sources`);
      setSources(response.data);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6">Loading sources...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Sources</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          {showForm ? 'Cancel' : 'Add Source'}
        </button>
      </div>

      {showForm && <SourceForm onSuccess={() => { fetchSources(); setShowForm(false); }} onCancel={() => setShowForm(false)} />}

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Commission</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sources.map((source) => (
              <tr key={source.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{source.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                    {source.source_type.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {source.contact_person || source.email || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {source.commission_rate ? `${source.commission_rate}%` : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(source.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sources.length === 0 && (
          <div className="text-center py-8 text-gray-500">No sources found</div>
        )}
      </div>
    </div>
  );
};

// Source Form Component
const SourceForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    source_type: 'consigner',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    commission_rate: '',
    payment_terms: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const submitData = {
        ...formData,
        contact_person: formData.contact_person || null,
        email: formData.email || null,
        phone: formData.phone || null,
        address: formData.address || null,
        commission_rate: formData.commission_rate ? parseFloat(formData.commission_rate) : null,
        payment_terms: formData.payment_terms || null,
        notes: formData.notes || null
      };

      await axios.post(`${API}/sources`, submitData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create source');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Source</h3>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
          <select
            name="source_type"
            value={formData.source_type}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="consigner">Consigner</option>
            <option value="estate_sale">Estate Sale</option>
            <option value="auction">Auction</option>
            <option value="private_seller">Private Seller</option>
            <option value="wholesale">Wholesale</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Contact Person</label>
          <input
            type="text"
            name="contact_person"
            value={formData.contact_person}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Commission Rate (%)</label>
          <input
            type="number"
            step="0.01"
            name="commission_rate"
            value={formData.commission_rate}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Payment Terms</label>
          <input
            type="text"
            name="payment_terms"
            value={formData.payment_terms}
            onChange={handleChange}
            placeholder="e.g., 30 days after sale, immediate, monthly"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="md:col-span-2 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Source'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Transactions Component (updated with clickable rows and add transaction)
const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [showTransactionForm, setShowTransactionForm] = useState(false);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTransactionClick = async (transaction) => {
    try {
      const response = await axios.get(`${API}/transactions/${transaction.id}/details`);
      setSelectedTransaction(response.data);
    } catch (error) {
      console.error('Failed to fetch transaction details:', error);
    }
  };

  if (loading) {
    return <div className="p-6">Loading transactions...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Transactions</h2>
        <button
          onClick={() => setShowTransactionForm(!showTransactionForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
        >
          {showTransactionForm ? 'Cancel' : 'Add Transaction'}
        </button>
      </div>

      {showTransactionForm && (
        <TransactionForm 
          onSuccess={() => { 
            fetchTransactions(); 
            setShowTransactionForm(false); 
          }} 
          onCancel={() => setShowTransactionForm(false)} 
        />
      )}

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.map((transaction) => (
              <tr 
                key={transaction.id} 
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => handleTransactionClick(transaction)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    transaction.transaction_type === 'sale' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {transaction.transaction_type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ${transaction.total_amount.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    transaction.status === 'completed' ? 'bg-green-100 text-green-800' :
                    transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {transaction.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{transaction.payment_method}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(transaction.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {transactions.length === 0 && (
          <div className="text-center py-8 text-gray-500">No transactions found</div>
        )}
      </div>

      {/* Transaction Detail Modal */}
      <Modal
        isOpen={!!selectedTransaction}
        onClose={() => setSelectedTransaction(null)}
        title="Transaction Details"
      >
        {selectedTransaction && <TransactionDetailView transaction={selectedTransaction} />}
      </Modal>
    </div>
  );
};

// Transaction Detail View Component
const TransactionDetailView = ({ transaction }) => {
  return (
    <div className="space-y-6">
      {/* Transaction Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Transaction Information</h3>
          <div className="space-y-2 text-sm">
            <p><span className="font-medium">Type:</span> {transaction.transaction.transaction_type}</p>
            <p><span className="font-medium">Status:</span> {transaction.transaction.status}</p>
            <p><span className="font-medium">Total Amount:</span> ${transaction.transaction.total_amount.toFixed(2)}</p>
            <p><span className="font-medium">Payment Method:</span> {transaction.transaction.payment_method}</p>
            {transaction.transaction.shipping_method && (
              <p><span className="font-medium">Shipping:</span> {transaction.transaction.shipping_method}</p>
            )}
            <p><span className="font-medium">Created:</span> {new Date(transaction.transaction.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Customer Information</h3>
          {transaction.customer ? (
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Name:</span> {transaction.customer.full_name}</p>
              <p><span className="font-medium">Email:</span> {transaction.customer.email || 'N/A'}</p>
              <p><span className="font-medium">Phone:</span> {transaction.customer.phone || 'N/A'}</p>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No customer information</p>
          )}
        </div>
      </div>

      {/* Notes */}
      {transaction.transaction.notes && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Notes</h3>
          <p className="text-sm text-gray-600">{transaction.transaction.notes}</p>
        </div>
      )}

      {/* Items */}
      {transaction.items && transaction.items.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Items</h3>
          <div className="space-y-3">
            {transaction.items.map((itemData, index) => (
              <div key={index} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    {itemData.product ? (
                      <div>
                        <p className="font-medium">{itemData.product.name}</p>
                        <p className="text-gray-600">{itemData.product.brand} - {itemData.product.code}</p>
                        <p className="text-gray-500">Condition: {itemData.product.condition}</p>
                      </div>
                    ) : (
                      <p className="text-gray-500">Product not found</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-medium">Qty: {itemData.item.quantity}</p>
                    <p className="text-gray-600">Unit: ${itemData.item.unit_price.toFixed(2)}</p>
                    <p className="font-semibold">Total: ${itemData.item.total_price.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Transaction Form Component
const TransactionForm = ({ onSuccess, onCancel }) => {
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [formData, setFormData] = useState({
    transaction_type: 'sale',
    customer_id: '',
    payment_method: '',
    shipping_method: '',
    notes: ''
  });
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCustomers();
    fetchProducts();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data.filter(p => p.status === 'available'));
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const addProduct = () => {
    setSelectedProducts([...selectedProducts, {
      product_id: '',
      quantity: 1,
      unit_price: 0
    }]);
  };

  const removeProduct = (index) => {
    setSelectedProducts(selectedProducts.filter((_, i) => i !== index));
  };

  const updateProductItem = (index, field, value) => {
    const updated = [...selectedProducts];
    updated[index][field] = field === 'quantity' ? parseInt(value) || 1 : 
                           field === 'unit_price' ? parseFloat(value) || 0 : value;
    
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        updated[index].unit_price = product.selling_price || product.purchase_price;
      }
    }
    
    setSelectedProducts(updated);
  };

  const calculateTotal = () => {
    return selectedProducts.reduce((total, item) => {
      return total + (item.quantity * item.unit_price);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (selectedProducts.length === 0) {
      setError('Please select at least one product');
      setLoading(false);
      return;
    }

    try {
      const submitData = {
        ...formData,
        shipping_method: formData.shipping_method || null,
        notes: formData.notes || null,
        items: selectedProducts.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price
        }))
      };

      await axios.post(`${API}/transactions`, submitData);
      onSuccess();
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create transaction');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Transaction</h3>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type *</label>
            <select
              name="transaction_type"
              value={formData.transaction_type}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="sale">Sale</option>
              <option value="purchase">Purchase</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Customer *</label>
            <select
              name="customer_id"
              value={formData.customer_id}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a customer</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.full_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method *</label>
            <select
              name="payment_method"
              value={formData.payment_method}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select payment method</option>
              <option value="cash">Cash</option>
              <option value="credit_card">Credit Card</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="check">Check</option>
              <option value="paypal">PayPal</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Shipping Method</label>
            <select
              name="shipping_method"
              value={formData.shipping_method}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select shipping method (optional)</option>
              <option value="pickup">Pickup</option>
              <option value="standard">Standard Shipping</option>
              <option value="express">Express Shipping</option>
              <option value="overnight">Overnight</option>
              <option value="white_glove">White Glove</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Products Section */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-medium text-gray-900">Products</h4>
            <button
              type="button"
              onClick={addProduct}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
            >
              Add Product
            </button>
          </div>

          {selectedProducts.map((item, index) => (
            <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 p-4 border rounded">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Product</label>
                <select
                  value={item.product_id}
                  onChange={(e) => updateProductItem(index, 'product_id', e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a product</option>
                  {products.map(product => (
                    <option key={product.id} value={product.id}>
                      {product.code} - {product.name} (${product.selling_price || product.purchase_price})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={item.quantity}
                  onChange={(e) => updateProductItem(index, 'quantity', e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit Price</label>
                <div className="flex">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={item.unit_price}
                    onChange={(e) => updateProductItem(index, 'unit_price', e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={() => removeProduct(index)}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-r-md"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          ))}

          {selectedProducts.length > 0 && (
            <div className="text-right">
              <p className="text-lg font-semibold">
                Total: ${calculateTotal().toFixed(2)}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || selectedProducts.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Transaction'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Tab Content Component
const TabContent = ({ activeTab }) => {
  switch (activeTab) {
    case 'dashboard':
      return <Dashboard />;
    case 'products':
      return <Products />;
    case 'customers':
      return <Customers />;
    case 'sources':
      return <Sources />;
    case 'transactions':
      return <Transactions />;
    default:
      return <Dashboard />;
  }
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <AuthWrapper />
      </div>
    </AuthProvider>
  );
}

// Auth Wrapper Component
const AuthWrapper = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <Navigation /> : <Login />;
};

export default App;