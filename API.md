# API Documentation - Event-Driven E-commerce Recommendation System

## Basic Information

- **Service Name**: E-commerce Recommendation System
- **Version**: 2.0.0
- **Architecture**: Serverless Event-Driven
- **Deployment**: AWS Lambda + API Gateway

## Performance Metrics

- **Order Processing**: < 3 seconds
- **Recommendation Generation**: < 500 milliseconds
- **Recommendation Query**: < 500 milliseconds

## API Endpoints

### 1. Health Check

Check if the service is running normally.

**Request**
```
GET /health
```

**Response**
```json
{
  "status": "healthy",
  "service": "E-commerce Recommendation System",
  "version": "2.0.0",
  "architecture": "serverless event-driven"
}
```

---

### 2. Create Order

Create a new order, automatically update inventory and publish events.

**Request**
```
POST /api/orders
Content-Type: application/json

{
  "user_id": "USER001",
  "items": [
    {
      "product_id": "PROD0001",
      "quantity": 2
    }
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "10001"
  }
}
```

**Response**
```json
{
  "success": true,
  "order_id": "ORD1234567890",
  "total_amount": 599.98,
  "processing_time_ms": 2450.5,
  "message": "Order created successfully"
}
```

**Error Response**
```json
{
  "error": "Insufficient inventory: PROD0001"
}
```

**Status Codes**
- `200`: Success
- `400`: Request parameter error or insufficient inventory
- `404`: Product not found
- `500`: Server error

---

### 3. Get Product List

Get product list with pagination and category filtering support.

**Request**
```
GET /api/products?category=Electronics&page=1&limit=20
```

**Query Parameters**
- `category` (optional): Product category
- `page` (optional): Page number, default 1
- `limit` (optional): Items per page, default 20

**Response**
```json
{
  "success": true,
  "data": [
    {
      "product_id": "PROD0001",
      "product_name": "Wireless Bluetooth Headphones",
      "category": "Electronics",
      "price": 299.99,
      "rating": 4.5,
      "image_url": "https://example.com/image.jpg",
      "description": "High-quality wireless Bluetooth headphones"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

### 4. Get Product Details

Get detailed information for a single product.

**Request**
```
GET /api/products/{product_id}
```

**Response**
```json
{
  "success": true,
  "data": {
    "product_id": "PROD0001",
    "product_name": "Wireless Bluetooth Headphones",
    "category": "Electronics",
    "price": 299.99,
    "rating": 4.5,
    "image_url": "https://example.com/image.jpg",
    "description": "High-quality wireless Bluetooth headphones",
    "tags": "bluetooth wireless noise-canceling music"
  }
}
```

---

### 5. Get User Recommendations

Get user's personalized recommendations (read from UserRecommendations table).

**Request**
```
GET /api/recommendations?user_id=USER001
```

**Query Parameters**
- `user_id` (required): User ID

**Response**
```json
{
  "success": true,
  "data": [
    {
      "product_id": "PROD0002",
      "product_name": "Smartphone",
      "category": "Electronics",
      "price": 2999.99,
      "rating": 4.7,
      "image_url": "https://example.com/image2.jpg",
      "score": 0.85
    }
  ],
  "count": 6,
  "generated_at": 1704067200,
  "response_time_ms": 125.5
}
```

**Error Response**
```json
{
  "error": "Recommendations not found for this user",
  "message": "Recommendations may be generating, please try again later"
}
```

**Note**: Recommendations are generated asynchronously by DynamoDB Streams, the first query may require waiting.

---

### 6. Record User Action

Record user actions (browse, click, search, etc.), write to DynamoDB and publish events.

**Request**
```
POST /api/user-actions
Content-Type: application/json

{
  "user_id": "USER001",
  "action_type": "view",
  "product_id": "PROD0001",
  "metadata": {
    "page": "product_detail",
    "duration": 30
  }
}
```

**Request Body Parameters**
- `user_id` (required): User ID
- `action_type` (required): Action type (`view`, `click`, `search`, `add_to_cart`)
- `product_id` (optional): Product ID
- `metadata` (optional): Additional metadata

**Response**
```json
{
  "success": true,
  "action_id": "USER001_1704067200000",
  "message": "User action recorded"
}
```

---

## Usage Examples

### cURL

```bash
# Health check
curl https://your-api-url/health

# Create order
curl -X POST https://your-api-url/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 1}],
    "shipping_address": {"city": "New York"}
  }'

# Get product list
curl "https://your-api-url/api/products?category=Electronics&page=1"

# Get recommendations
curl "https://your-api-url/api/recommendations?user_id=USER001"

# Record user action
curl -X POST https://your-api-url/api/user-actions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER001",
    "action_type": "view",
    "product_id": "PROD0001"
  }'
```

### Python

```python
import requests

BASE_URL = "https://your-api-url"

# Create order
order_data = {
    "user_id": "USER001",
    "items": [{"product_id": "PROD0001", "quantity": 2}],
    "shipping_address": {"city": "New York"}
}
response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
order = response.json()
print(f"Order ID: {order['order_id']}")
print(f"Processing Time: {order['processing_time_ms']}ms")

# Get recommendations
response = requests.get(f"{BASE_URL}/api/recommendations", 
                       params={"user_id": "USER001"})
recommendations = response.json()['data']
print(f"Recommendation Count: {len(recommendations)}")
```

### JavaScript

```javascript
const BASE_URL = 'https://your-api-url';

// Create order
fetch(`${BASE_URL}/api/orders`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'USER001',
    items: [{ product_id: 'PROD0001', quantity: 2 }],
    shipping_address: { city: 'New York' }
  })
})
  .then(res => res.json())
  .then(data => {
    console.log(`Order ID: ${data.order_id}`);
    console.log(`Processing Time: ${data.processing_time_ms}ms`);
  });

// Get recommendations
fetch(`${BASE_URL}/api/recommendations?user_id=USER001`)
  .then(res => res.json())
  .then(data => {
    console.log(`Recommendation Count: ${data.count}`);
    console.log(`Response Time: ${data.response_time_ms}ms`);
  });
```

## Event Flow

### Order Creation Event Flow

1. **Client** → `POST /api/orders`
2. **Order Handler Lambda**:
   - Validate inventory (atomic operation)
   - Create order (DynamoDB)
   - Update inventory
   - Publish event to EventBridge
3. **DynamoDB Streams** trigger
4. **Recommendation Generator Lambda**:
   - Analyze order history
   - Generate recommendations
   - Store in UserRecommendations table

### User Action Event Flow

1. **Client** → `POST /api/user-actions`
2. **User Action Handler Lambda**:
   - Write to UserActions table
   - Publish event to EventBridge

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Request parameter error |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service temporarily unavailable |

## CORS

All endpoints support CORS and can be accessed from any domain.

## Performance Monitoring

### Key Metrics

- **Order Processing Time**: Target < 3s
- **Recommendation Generation Time**: Target < 500ms
- **Recommendation Query Time**: Target < 500ms

### Monitoring Methods

- CloudWatch Logs: View Lambda execution logs
- CloudWatch Metrics: View performance metrics
- Custom Metrics: Include processing time in responses

## Notes

1. **Recommendation Generation**: Recommendations are generated asynchronously by DynamoDB Streams, the first query may require waiting
2. **Inventory Updates**: Use atomic operations to ensure data consistency
3. **Event Ordering**: EventBridge events may not guarantee order
4. **Cold Start**: Lambda cold start may affect first request performance

## Version History

- **v2.0.0**: Event-driven architecture, DynamoDB Streams integration
- **v1.0.0**: Initial version, basic recommendation functionality
