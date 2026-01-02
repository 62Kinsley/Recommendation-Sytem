# Quick Start Guide

## 5-Minute Quick Deployment

### Step 1: Prepare Environment

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Create Data and Train Model

```bash
# Create sample product data
python create_sample_data.py

# Train recommendation model
python train_model.py
```

### Step 3: Configure AWS

```bash
# Configure AWS credentials
aws configure
```

You need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., ap-northeast-1)
- Output format (json)

### Step 4: Deploy

```bash
# Method 1: Use deployment script (recommended)
./deploy.sh

# Method 2: Manual deployment
npm run deploy
```

### Step 5: Upload Models

After deployment, get the S3 bucket name from the output, then upload models:

```bash
# Replace <bucket-name> with the actual bucket name
aws s3 cp models/ s3://<bucket-name>/models/ --recursive
```

### Step 6: Test API

Get the API Gateway URL from the deployment output, then test:

```bash
# Health check
curl https://<your-api-url>/health

# Get recommendations
curl "https://<your-api-url>/api/recommendations?user_id=USER001"
```

## Local Testing

You can test locally before deployment:

```bash
python test_local.py
```

## Common Issues

### Q: Deployment fails with insufficient permissions
A: Check AWS IAM permissions, ensure you have:
- Lambda-related permissions
- S3-related permissions
- API Gateway permissions
- CloudFormation permissions

### Q: Model files are too large, upload fails
A: You can:
1. Reduce the number of products
2. Use Lambda Layers to store large dependencies
3. Optimize model parameters (reduce feature count)

### Q: Lambda function times out
A: Increase the `timeout` value in `serverless.yml`, or optimize model loading logic.

## Next Steps

- View [API.md](API.md) for complete API documentation
- View [README.md](README.md) for detailed configuration
- Modify recommendation algorithms according to actual needs
