echo "Building and Pushing Docker Image to ECR"
docker buildx build --platform linux/arm64 -f dockerfile.nango  -t 990005967194.dkr.ecr.us-east-1.amazonaws.com/nango-caller-agent:latest .

echo "Logging in to AWS ECR"
docker push 990005967194.dkr.ecr.us-east-1.amazonaws.com/nango-caller-agent:latest                                                         