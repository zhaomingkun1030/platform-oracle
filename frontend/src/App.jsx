import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout, message } from 'antd'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './App.css'

const { Content } = Layout

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  }, [token])

  const handleLogout = () => {
    setToken(null)
    localStorage.removeItem('token')
    message.success('已退出登录')
  }

  return (
    <BrowserRouter>
      <Layout className="app-layout">
        <Content className="app-content">
          <Routes>
            <Route 
              path="/login" 
              element={
                token ? <Navigate to="/" replace /> : <Login setToken={setToken} />
              } 
            />
            <Route 
              path="/" 
              element={
                token ? <Dashboard token={token} onLogout={handleLogout} /> : <Navigate to="/login" replace />
              } 
            />
          </Routes>
        </Content>
      </Layout>
    </BrowserRouter>
  )
}

export default App
