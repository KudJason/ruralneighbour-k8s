#!/bin/bash

# Rural Neighbor Connect - Kubernetes Deployment Script
# This script deploys all microservices to Kubernetes

set -e

echo "🚀 Starting Rural Neighbor Connect deployment..."

# Create namespace if it doesn't exist
kubectl create namespace default --dry-run=client -o yaml | kubectl apply -f -

echo "📦 Deploying shared infrastructure..."

# Deploy shared secrets and configs
kubectl apply -f _shared/postgres-secrets.yaml
kubectl apply -f _shared/redis-secrets.yaml

# Deploy infrastructure services
kubectl apply -f _shared/postgres-deployment.yaml
kubectl apply -f _shared/redis-deployment.yaml

echo "⏳ Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis-service --timeout=300s

echo "🔧 Deploying microservices..."

# Deploy microservices
kubectl apply -f auth-service/
kubectl apply -f user-service/
kubectl apply -f location-service/
kubectl apply -f request-service/
kubectl apply -f payment-service/
kubectl apply -f notification-service/
kubectl apply -f content-service/
kubectl apply -f safety-service/

echo "⏳ Waiting for microservices to be ready..."
kubectl wait --for=condition=ready pod -l app=auth-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=user-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=location-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=request-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=notification-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=content-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=safety-service --timeout=300s

echo "🌐 Deploying API Gateway..."
kubectl apply -f _shared/ingress.yaml

echo "✅ Deployment completed successfully!"

echo ""
echo "📊 Deployment Status:"
kubectl get pods -l tier=backend
kubectl get pods -l tier=database
kubectl get pods -l tier=cache

echo ""
echo "🌍 Services:"
kubectl get services -l tier=backend

echo ""
echo "🔗 Ingress:"
kubectl get ingress

echo ""
echo "📝 To access the application:"
echo "1. Make sure you have an Ingress controller installed (e.g., nginx-ingress)"
echo "2. The API will be available at: http://your-cluster-ip/api/v1/"
echo "3. Health check: http://your-cluster-ip/health" 