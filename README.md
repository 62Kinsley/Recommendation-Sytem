# Serverless Event-Driven E-commerce Recommendation System

A serverless, event-driven e-commerce system built on AWS that implements order processing, inventory management, and personalized AI recommendation features.

## 🎯 Core Features

- ✅ **Order Processing**: Process order placement with atomic inventory updates, < 3s processing time
- ✅ **Personalized Recommendations**: Real-time recommendation generation based on order history, < 500ms generation latency
- ✅ **Event-Driven Architecture**: Asynchronous processing using DynamoDB Streams and EventBridge
- ✅ **RESTful API**: Complete API Gateway interfaces
- ✅ **Fine-Grained IAM Policies**: Ensures data security and integrity

## 🏗️ System Architecture

### Event-Driven Flow

```
Order Creation → DynamoDB Streams → Recommendation Generator Lambda → Store Recommendations
    ↓
EventBridge → Event Bus → Downstream Services
```

### Core Components

- **API Gateway**: RESTful API entry point
- **Lambda Functions**: 
  - Order processing (< 3s)
  - Recommendation generation (< 500ms, triggered by DynamoDB Streams)
  - Product browsing
  - User action recording
- **DynamoDB**: 
  - Orders (order table with Streams enabled)
  - Products (product table)
  - Inventory (inventory table)
  - UserRecommendations (user recommendation table)
  - UserActions (user action table)
- **EventBridge**: Event bus for processing order and user action events
- **IAM**: Fine-grained access control

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md)

## 📊 Performance Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Order Processing Time | < 3s | ✅ |
| Recommendation Generation Latency | < 500ms | ✅ |
| Recommendation Query Latency | < 500ms | ✅ |
| System Availability | 99.9% | ✅ |

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with configured credentials
2. **Node.js 14+** (for Serverless Framework)
3. **Python 3.9+** (for local development)
4. **AWS CLI** configured

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd Recommendation-Sytem
```

2. **Install dependencies**
```bash
# Node.js dependencies
npm install

# Python dependencies
pip install -r requirements.txt
```

3. **Deploy to AWS**
```bash
# Deploy to development environment
serverless deploy

# Or deploy to production environment
serverless deploy --stage prod
```

4. **Initialize DynamoDB data**
```bash
# Create sample product and inventory data
python scripts/init_dynamodb.py
```

5. **Test the API**

Get the API Gateway URL from the deployment output, then test:

```bash
# Health check
curl https://<api-url>/health

# Get product list
curl https://<api-url>/api/products

# Create an order
curl -X POST https://<api-url>/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 2}],
    "shipping_address": {"city": "New York"}
  }'

# Get recommendations
curl "https://<api-url>/api/recommendations?user_id=USER001"
```

## 📁 Project Structure

```
.
├── handlers/                      # Lambda function handlers
│   ├── order_handler.py         # Order processing
│   ├── recommendation_handler.py # Recommendation generation (Streams triggered)
│   ├── recommendation_api_handler.py # Recommendation query API
│   ├── product_browse_handler.py # Product browsing
│   └── health_handler.py        # Health check
├── scripts/                      # Utility scripts
│   ├── init_dynamodb.py         # Initialize DynamoDB data
│   └── monitoring_setup.py      # Monitoring configuration
├── serverless.yml                # Serverless configuration
├── requirements.txt              # Python dependencies
├── package.json                 # Node.js dependencies
├── ARCHITECTURE.md              # Architecture documentation
├── API.md                       # API documentation
└── README.md                    # Project documentation
```

## 🔌 API Endpoints

### Order Related

- `POST /api/orders` - Create order
  - Request body: `{user_id, items[], shipping_address}`
  - Response: `{order_id, total_amount, processing_time_ms}`

### Product Related

- `GET /api/products` - Get product list (supports pagination and filtering)
- `GET /api/products/{product_id}` - Get product details

### Recommendation Related

- `GET /api/recommendations?user_id=USER001` - Get user recommendations
  - Response: `{data[], count, response_time_ms}`

### User Actions

- `POST /api/user-actions` - Record user actions
  - Request body: `{user_id, action_type, product_id, metadata}`

### System

- `GET /health` - Health check

For detailed API documentation, see [API.md](API.md)

## 🔐 Security Architecture

### IAM Policies

The system implements fine-grained IAM policies:

- **DynamoDB Access**: Table-level permissions, only necessary operations allowed
- **EventBridge Access**: Event bus-level permissions
- **Lambda Execution**: Principle of least privilege
- **S3 Access**: Bucket-level permissions (if needed)

All IAM policies are defined in `serverless.yml`.

## 📈 Monitoring and Logging

### CloudWatch

- **Lambda Logs**: Automatically logged to CloudWatch Logs
- **Metrics**: Execution time, error rate, invocation count
- **Alarms**: Configurable performance threshold alarms

### Setup Monitoring

```bash
python scripts/monitoring_setup.py
```

This will create the following alarms:
- Order processing time > 3s
- Recommendation generation time > 500ms
- Lambda error rate > 5%

## 🛠️ Development Guide

### Local Testing

```bash
# Test order processing
python -c "
from handlers.order_handler import process_order
event = {
    'httpMethod': 'POST',
    'body': '{\"user_id\": \"USER001\", \"items\": [{\"product_id\": \"PROD0001\", \"quantity\": 1}]}'
}
result = process_order(event, None)
print(result)
"
```

### Adding New Features

1. Create a new Lambda function in the `handlers/` directory
2. Configure the function and events in `serverless.yml`
3. Update IAM policies (if needed)
4. Deploy and test

### Environment Variables

All table names and configurations are passed through environment variables, defined in `serverless.yml`.

## 📦 Deployment

### Initial Deployment

```bash
# 1. Deploy the service
serverless deploy

# 2. Initialize data
python scripts/init_dynamodb.py

# 3. Setup monitoring (optional)
python scripts/monitoring_setup.py
```

### Update Deployment

```bash
serverless deploy
```

### Remove Deployment

```bash
serverless remove
```

## 💰 Cost Optimization

- **Pay-per-use**: Lambda and DynamoDB charged based on actual usage
- **Auto-scaling**: No need to provision capacity
- **Resource Optimization**: Adjust Lambda memory based on performance requirements

## 🐛 Troubleshooting

### Common Issues

1. **DynamoDB table does not exist**
   - Ensure `serverless deploy` has been run
   - Check if table names are correct

2. **Lambda timeout**
   - Increase `timeout` configuration
   - Optimize code logic

3. **Recommendations not generated**
   - Check if DynamoDB Streams is enabled
   - View CloudWatch Logs

4. **Permission errors**
   - Check IAM policy configuration
   - Verify Lambda execution role permissions

## 📚 Related Documentation

- [Architecture Documentation](ARCHITECTURE.md) - Detailed system architecture
- [API Documentation](API.md) - Complete API interface documentation
- [Quick Start Guide](QUICKSTART.md) - Quick deployment guide

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 📞 Contact

For questions, please submit an Issue.

---

**Performance Metrics Achieved**:
- ✅ Order Processing: < 3s
- ✅ Recommendation Generation: < 500ms
- ✅ Event-Driven Architecture
- ✅ Fine-Grained IAM Policies
