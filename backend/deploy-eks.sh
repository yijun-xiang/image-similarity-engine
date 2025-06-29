#!/bin/bash
set -e

CLUSTER_NAME="image-similarity-eks"
REGION="us-east-1"
NODE_TYPE="t3.medium"
NODES=2

echo "Installing eksctl..."
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

echo "Creating EKS cluster..."
eksctl create cluster \
    --name $CLUSTER_NAME \
    --region $REGION \
    --node-type $NODE_TYPE \
    --nodes $NODES \
    --nodes-min 1 \
    --nodes-max 3 \
    --managed

echo "Configuring kubectl..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

echo "Installing AWS Load Balancer Controller..."
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.5.4/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json 2>/dev/null || true

eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --role-name AmazonEKSLoadBalancerControllerRole \
    --attach-policy-arn=arn:aws:iam::035711439189:policy/AWSLoadBalancerControllerIAMPolicy \
    --approve

kubectl apply \
    --validate=false \
    -f https://github.com/jetstack/cert-manager/releases/download/v1.12.0/cert-manager.yaml

sleep 30

curl -Lo v2_5_4_full.yaml https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.5.4/v2_5_4_full.yaml
sed -i.bak -e 's|your-cluster-name|'$CLUSTER_NAME'|' v2_5_4_full.yaml
kubectl apply -f v2_5_4_full.yaml

echo "Deploying application..."
kubectl create namespace image-similarity

cat > k8s-deployment.yaml <<K8S
apiVersion: v1
kind: Namespace
metadata:
  name: image-similarity
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: image-similarity
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command: ["redis-server", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: image-similarity
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: image-similarity
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.14.0
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
      volumes:
      - name: qdrant-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: image-similarity
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: image-similarity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: 035711439189.dkr.ecr.us-east-1.amazonaws.com/image-similarity:latest
        ports:
        - containerPort: 8000
        env:
        - name: QDRANT_HOST
          value: qdrant
        - name: REDIS_HOST
          value: redis
        - name: APP_NAME
          value: "Image Similarity Engine"
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: image-similarity
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  namespace: image-similarity
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
K8S

kubectl apply -f k8s-deployment.yaml

echo "Waiting for load balancer..."
sleep 60

LB_URL=$(kubectl get service backend -n image-similarity -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Application URL: http://$LB_URL"
echo "Health Check: http://$LB_URL/api/v1/health"
