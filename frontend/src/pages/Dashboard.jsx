import React, { useState, useEffect } from 'react'
import { 
  Layout, 
  Table, 
  Button, 
  Input, 
  Space, 
  Tag, 
  Typography, 
  message, 
  Modal,
  Spin,
  Divider
} from 'antd'
import { 
  PlayCircleOutlined, 
  DeleteOutlined, 
  DownloadOutlined,
  LogoutOutlined,
  LinkOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Header } = Layout
const { Title } = Typography
const { TextArea } = Input

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function Dashboard({ token, onLogout }) {
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [url, setUrl] = useState('')

  const api = axios.create({
    baseURL: API_BASE,
    headers: { Authorization: `Bearer ${token}` }
  })

  useEffect(() => {
    fetchAnalyses()
  }, [])

  const fetchAnalyses = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/analyses')
      setAnalyses(response.data)
    } catch (error) {
      message.error('获取分析记录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!url.trim()) {
      message.warning('请输入 URL')
      return
    }

    setAnalyzing(true)
    try {
      const response = await api.post('/api/analyses', {
        url: url,
        analyst: 'admin'
      })
      
      message.success('分析任务已启动')
      setUrl('')
      fetchAnalyses()
    } catch (error) {
      message.error(error.response?.data?.detail || '分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDelete = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条分析记录吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/api/analyses/${id}`)
          message.success('删除成功')
          fetchAnalyses()
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const handleDownload = (filename) => {
    const link = document.createElement('a')
    link.href = `${API_BASE}/api/reports/${filename}`
    link.download = filename
    link.click()
  }

  const columns = [
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      render: (url) => (
        <a href={url} target="_blank" rel="noopener noreferrer">
          <LinkOutlined /> {url.substring(0, 50)}...
        </a>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'completed' ? 'green' : status === 'failed' ? 'red' : 'blue'}>
          {status === 'completed' ? '已完成' : status === 'failed' ? '失败' : '处理中'}
        </Tag>
      )
    },
    {
      title: '启动时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (time) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '完成时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (time) => time ? new Date(time).toLocaleString('zh-CN') : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {record.report_file && (
            <Button 
              type="link" 
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.report_file)}
            >
              下载报告
            </Button>
          )}
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px' }}>
        <Title level={4} style={{ color: 'white', margin: 0 }}>
          Platform Oracle - OpenShift 竞品分析
        </Title>
        <Button 
          type="text" 
          icon={<LogoutOutlined />} 
          onClick={onLogout}
          style={{ color: 'white' }}
        >
          退出
        </Button>
      </Header>
      
      <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        {/* 分析输入区域 */}
        <div style={{ background: '#fff', padding: '24px', borderRadius: 8, marginBottom: 24 }}>
          <Title level={5}>创建新分析</Title>
          <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
            <Input
              placeholder="输入 OpenShift URL (如 https://docs.openshift.com/...)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onPressEnter={handleAnalyze}
              suffix={<LinkOutlined />}
            />
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={handleAnalyze}
              loading={analyzing}
              disabled={!url.trim()}
            >
              {analyzing ? '分析中...' : '立即分析'}
            </Button>
          </Space.Compact>
          <TextArea 
            placeholder="分析将自动提取功能点、竞品策略解释，并生成 Roadmap 预测"
            rows={2} 
            disabled 
            style={{ background: '#f5f5f5' }}
          />
        </div>

        <Divider />

        {/* 分析记录列表 */}
        <div style={{ background: '#fff', padding: '24px', borderRadius: 8 }}>
          <Title level={5}>分析记录</Title>
          <Table
            columns={columns}
            dataSource={analyses}
            rowKey="id"
            loading={loading}
            locale={{ emptyText: '暂无分析记录' }}
          />
        </div>
      </div>
    </Layout>
  )
}

export default Dashboard
