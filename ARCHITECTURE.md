# System Architecture Documentation

## Overview

This is a serverless, event-driven e-commerce recommendation system built on AWS that implements order processing, inventory management, and personalized AI recommendation features.

## Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │
┌──────▼─────────────────────────────────────────────┐
│              API Gateway                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ /orders  │  │/products │  │/recommend│        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼──────────────┼──────────────┘
        │             │              │
        │             │              │
┌───────▼──────┐  ┌───▼──────┐  ┌───▼──────────────┐
│ Order Handler│  │  Product │  │ Recommendation  │
│   Lambda     │  │  Lambda  │  │   API Lambda    │
└──────┬───────┘  └──────────┘  └─────────────────┘
       │
       │ 1. Write order
       │ 2. Update inventory
       │ 3. Publish event
       │
┌──────▼─────────────────────────────────────────────┐
│              DynamoDB Tables                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Orders  │  │ Products │  │Inventory │        │
│  └────┬─────┘  └──────────┘  └──────────┘        │
└───────┼────────────────────────────────────────────┘
        │
        │ DynamoDB Streams
        │
┌───────▼────────────────────────────────────────────┐
│    Recommendation Generator Lambda                  │
│    (Trigger: New order creation)                   │
│    - Analyze order history                        │
│    - Generate personalized recommendations        │
│    - Target: < 500ms                              │
└───────┬────────────────────────────────────────────┘
        │
        │ Write recommendations
        │
┌───────▼────────────────────────────────────────────┐
│         UserRecommendations Table                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│              EventBridge Event Bus                 │
│  - Order Placed Events                             │
│  - User Action Events                              │
└────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway
- **Function**: RESTful API entry point
- **Routes**:
  - `POST /api/orders` - Create order
  - `GET /api/products` - Get product list
  - `GET /api/products/{product_id}` - Get product details
  - `GET /api/recommendations` - Get user recommendations
  - `POST /api/user-actions` - Record user actions
  - `GET /health` - Health check

### 2. Lambda Functions

#### Order Handler
- **Function**: Handle order creation
- **Process**:
  1. Validate inventory (atomic operation)
  2. Create order record (DynamoDB)
  3. Update inventory
  4. Publish event to EventBridge
- **Performance Target**: < 3s
- **Memory**: 1024 MB
- **Timeout**: 10s

#### Recommendation Generator
- **Function**: Generate personalized recommendations
- **Trigger**: DynamoDB Streams (Orders table)
- **Process**:
  1. Analyze user order history
  2. Calculate product similarity
  3. Generate recommendation list
  4. Store in UserRecommendations table
- **Performance Target**: < 500ms
- **Memory**: 2048 MB
- **Timeout**: 15s

#### Recommendation API
- **Function**: Provide recommendation query interface
- **Performance Target**: < 500ms
- **Memory**: 512 MB
- **Timeout**: 5s

#### Product Browse Handler
- **Function**: Product browsing and search
- **Memory**: 512 MB
- **Timeout**: 5s

#### User Action Handler
- **Function**: Record user actions
- **Process**:
  1. Write to DynamoDB
  2. Publish event to EventBridge

### 3. DynamoDB Tables

#### Orders Table
- **Primary Key**: `order_id` (String)
- **GSI**: `user_id-created_at-index`
- **Streams**: Enabled (NEW_AND_OLD_IMAGES)
- **Purpose**: Store order information

#### Products Table
- **Primary Key**: `product_id` (String)
- **Purpose**: Store product information

#### Inventory Table
- **Primary Key**: `product_id` (String)
- **Purpose**: Inventory management (atomic updates)

#### UserRecommendations Table
- **Primary Key**: `user_id` (String)
- **Purpose**: Store user personalized recommendations

#### UserActions Table
- **Primary Key**: `action_id` (String)
- **Purpose**: Record user actions (browse, click, etc.)

### 4. EventBridge
- **Event Bus**: `ecommerce-events-{stage}`
- **Event Types**:
  - `Order Placed` - Order creation
  - `User Action` - User behavior

### 5. DynamoDB Streams
- **Table**: Orders
- **View Type**: NEW_AND_OLD_IMAGES
- **Purpose**: Trigger recommendation generation Lambda

## Data Flow

### Order Processing Flow

1. **Client Request** → API Gateway → Order Handler Lambda
2. **Validate Inventory**: Use DynamoDB conditional update (atomic operation)
3. **Create Order**: Write to Orders table
4. **Update Inventory**: Atomically decrease inventory quantity
5. **Publish Event**: Send to EventBridge
6. **Return Response**: Order ID and processing time

### Recommendation Generation Flow

1. **Order Creation** → DynamoDB Streams trigger
2. **Recommendation Generator Lambda** is triggered
3. **Query Order History**: Get user's recent orders from Orders table
4. **Analyze Purchase Patterns**: Extract category preferences
5. **Generate Recommendations**: Based on category similarity, ratings, price
6. **Store Recommendations**: Write to UserRecommendations table

### Recommendation Query Flow

1. **Client Request** → API Gateway → Recommendation API Lambda
2. **Query Recommendations**: Read from UserRecommendations table
3. **Return Results**: JSON-formatted recommendation list

## Performance Metrics

### Target Performance
- **Order Processing**: < 3 seconds
- **Recommendation Generation**: < 500 milliseconds
- **Recommendation Query**: < 500 milliseconds

### Optimization Strategies
1. **Lambda Container Reuse**: Cache connections using global variables
2. **DynamoDB On-Demand Billing**: Auto-scaling
3. **Batch Processing**: DynamoDB Streams batch triggers
4. **Memory Optimization**: Allocate memory based on function requirements
5. **Connection Pooling**: Reuse boto3 clients

## Security Architecture

### IAM Policies
- **Principle of Least Privilege**: Each Lambda only accesses necessary resources
- **Fine-Grained Control**:
  - DynamoDB: Table-level permissions
  - EventBridge: Event bus-level permissions
  - S3: Bucket-level permissions

### Data Security
- **Encryption**: DynamoDB table encryption (enabled by default)
- **Access Control**: IAM roles and policies
- **Network**: API Gateway provides HTTPS

## Monitoring and Logging

### CloudWatch
- **Lambda Logs**: Automatically logged
- **Metrics**: Execution time, error rate, invocation count
- **Alarms**: Configurable performance threshold alarms

### Custom Metrics
- Order processing time
- Recommendation generation time
- Recommendation query time

## Scalability

### Horizontal Scaling
- **Lambda**: Auto-scaling, unlimited concurrency
- **DynamoDB**: On-demand billing, auto-scaling
- **API Gateway**: Automatically handles high concurrency

### Vertical Scaling
- **Memory Adjustment**: Adjust Lambda memory based on performance requirements
- **Timeout Settings**: Adjust based on processing time

## Cost Optimization

1. **Pay-per-use**: Only pay for actual usage
2. **Lambda Optimization**: Reduce execution time and memory usage
3. **DynamoDB On-Demand**: No need to provision capacity
4. **API Gateway**: Pay per request

## Error Handling

### Error Handling
- **Insufficient Inventory**: Return 400 error
- **Product Not Found**: Return 404 error
- **System Error**: Return 500 error, log details

### Retry Mechanism
- **DynamoDB Streams**: Automatically retry failed records
- **EventBridge**: Configurable retry strategy

## Deployment

### Environments
- **Development Environment**: `dev`
- **Production Environment**: `prod`

### Deployment Steps
1. Install dependencies: `npm install`
2. Deploy service: `serverless deploy`
3. Initialize data: `python scripts/init_dynamodb.py`
