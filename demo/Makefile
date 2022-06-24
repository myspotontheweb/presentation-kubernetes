
SEQ=1
NAME=scoil
PROJECT=myspotontheweb
SUBSCRIPTION=88e83753-dd99-4ebe-9bf1-dd7758216554
REGION=eastus
RESOURCE_GROUP=$(NAME)-${LOGNAME}-$(SEQ)
REGISTRY=$(NAME)$(SEQ).azurecr.io
CLUSTER=$(NAME)-$(SEQ)
NODES=2

TAG=$(shell git describe)
REPOSITORY=$(REGISTRY)/$(PROJECT)/$(NAME)$(SEQ)
RELEASE=$(NAME)
HELM_PATH=chart
NAMESPACE=${LOGNAME}

default: build

#
# Build (using docker)
#
build:
	docker build -t $(REPOSITORY):$(TAG) .
	docker push $(REPOSITORY):$(TAG)

#
# Deploy (using helm)
#
deploy:
	helm upgrade $(RELEASE) $(HELM_PATH) --install --set image.repository=$(REPOSITORY) --set image.tag=$(TAG) --namespace $(NAMESPACE) --create-namespace

render:
	helm template $(RELEASE) $(HELM_PATH) --set image.repository=$(REPOSITORY) --set image.tag=$(TAG)

#
# Auth
#
login:
	az login

creds: creds-cluster creds-registry

creds-cluster:
	az aks get-credentials --resource-group $(RESOURCE_GROUP) --name $(CLUSTER)

creds-registry:
	az acr login --name $(REGISTRY)

#
# Cluster provisioning targets
#
provision: provision-registry provision-aks-cluster 

provision-setup:
	az account set --subscription $(SUBSCRIPTION)
	az group create --name $(RESOURCE_GROUP) --location $(REGION)

provision-registry: provision-setup
	az acr create --resource-group $(RESOURCE_GROUP) --name $(NAME)$(SEQ) --sku Basic

provision-aks-cluster:
	az aks create --resource-group $(RESOURCE_GROUP) --name $(CLUSTER) --node-count $(NODES) --attach-acr $(NAME)$(SEQ) 

#
# Purge infrastructure
#
clean:
	az group delete --name $(RESOURCE_GROUP) --yes --no-wait

